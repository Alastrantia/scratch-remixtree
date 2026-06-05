import sys
import os
import time
import asyncio
import aiohttp
import io

from .api import get_root_id, fetch_project_data
from .tree_builder import build_remix_tree
from .node import extract_metadata, fmt_count
from . import export
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich import box
from .cli import parse_args

# force utf8 on windows so my tests dont fail bahhhh
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

console = Console()

# how many nodes we draw in the on-screen preview before going "... use -o for the rest"
PREVIEW_NODE_CAP = 80


def output_path_for(base, project_id, multiple):
    """when batching we cant dump every tree into the same file, so stick the id in: tree.txt -> tree_123.txt"""
    if not multiple:
        return base
    root, ext = os.path.splitext(base)
    return f"{root}_{project_id}{ext}"


def stats_table(start_id, root_id, root_remix_count, total_nodes, max_depth, elapsed, root_node):
    """the little summary box at the end, way nicer than a wall of print()s"""
    table = Table(show_header=False, box=box.ROUNDED, border_style="green", expand=False)
    table.add_column(style="cyan", justify="right")
    table.add_column(style="bold")
    table.add_row("start project", str(start_id))
    table.add_row("original (root)", str(root_id))
    table.add_row("direct remixes", str(root_remix_count))
    table.add_row("projects found", f"{total_nodes} (root + all the kids!)")
    table.add_row("deepest level", str(max_depth))
    table.add_row("time taken", f"{elapsed:.2f}s")
    if root_node.likes or root_node.views or root_node.favorites:
        table.add_row(
            "root stats",
            f"♥{fmt_count(root_node.likes)}  \U0001f441{fmt_count(root_node.views)}  ★{fmt_count(root_node.favorites)}",
        )
    return table


async def process_project(session, project_id, args, index=None, total=None):
    """do the whole thing for a single project id. returns True on success."""
    multiple = bool(total and total > 1)

    label = f"[bold cyan]#BringBackRemixTrees[/bold cyan] (ID: {project_id})"
    if multiple:
        label = f"[dim][{index}/{total}][/dim] " + label
    console.print(Panel(label, expand=False, border_style="cyan"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task1 = progress.add_task("Figuring out where the original project is...", total=None)
        root = await get_root_id(session, project_id)
        progress.update(task1, completed=True)

        task2 = progress.add_task("Getting the stats for the main project...", total=None)
        root_data = await fetch_project_data(session, root)
        if not root_data:
            progress.update(task2, completed=True)
            console.print(f"[bold red]✗ Couldn't fetch project {root}, skipping this one.[/bold red]")
            return False
        progress.update(task2, completed=True)

    root_remix_count = root_data.get("stats", {}).get("remixes", 0)
    root_title = root_data.get("title")
    root_meta = extract_metadata(root_data)

    console.print()
    console.print(f"[bold]Start Project ID:[/bold] {project_id}")
    console.print(f"[bold]OG Project ID:[/bold] [yellow]{root}[/yellow] (Total direct remixes: [bold]{root_remix_count}[/bold])")
    if args.depth:
        console.print(f"[bold]We'll only go this deep (Max depth):[/bold] {args.depth}")
    if args.output:
        console.print(f"[bold]Saving the full result to:[/bold] [green]{output_path_for(args.output, project_id, multiple)}[/green]")
    if args.color:
        console.print("[bold]Using color mode![/bold]")
    console.print()

    if root_remix_count > 5000:
        console.print("[bold yellow](Pray for the Scratch Servers)[/bold yellow] This tree is huge, it's gonna take a bit. In the meantime, follow Joshisaurio on Scratch!")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task3 = progress.add_task(f"[cyan]Building the tree, starting from {root}...", total=None)
        start_time = time.perf_counter()
        tree = await build_remix_tree(
            session, root, root_title, args.depth,
            progress=progress, verbose=args.verbose, **root_meta,
        )
        end_time = time.perf_counter()
        tree.sort_children_by_share_date(reverse=True)  # newest first
        progress.update(task3, completed=True)

    elapsed_time = end_time - start_time
    total_nodes = tree.count_nodes()

    console.print()
    console.print(Panel("[bold green]All done! We found everything.[/bold green]", expand=False, border_style="green"))
    console.print(stats_table(project_id, root, root_remix_count, total_nodes, tree.max_depth(), elapsed_time, tree))

    if args.output:
        out_path = output_path_for(args.output, project_id, multiple)
        fmt = args.format or export.format_from_extension(args.output, default="txt")
        try:
            content = export.export(tree, fmt, show_stats=args.stats)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"[bold green]✓ Success:[/bold green] Full tree ([cyan]{fmt}[/cyan]) saved to [yellow]{out_path}[/yellow].")
        except Exception as e:
            console.print(f"[bold red]✗ FILE ERROR:[/bold red] Couldn't save to {out_path}: {e}")
    else:
        console.print("\n[bold]--- Tree Structure Preview ---[/bold]")
        console.print(tree.to_rich_tree(color=args.color, show_stats=args.stats, max_nodes=PREVIEW_NODE_CAP))
        if total_nodes > PREVIEW_NODE_CAP:
            console.print("[dim]... (The rest is long! Use -o to save the full structure, e.g. -o tree.json)[/dim]")

    return True


async def main():
    args = parse_args()
    try:
        timeout_config = aiohttp.ClientTimeout(total=args.timeout)
        connector = aiohttp.TCPConnector(limit=50)
        async with aiohttp.ClientSession(timeout=timeout_config, connector=connector) as session:
            total = len(args.project_ids)
            ok = 0
            for i, project_id in enumerate(args.project_ids, start=1):
                if i > 1:
                    console.print()
                if await process_project(session, project_id, args, index=i, total=total):
                    ok += 1
            if total > 1:
                console.print()
                console.print(f"[bold green]Batch done![/bold green] {ok}/{total} trees built successfully.")
    except Exception as e:
        console.print(f"\n[bold red]✗ SOMETHING BROKE:[/bold red] An unexpected error happened: {e}")
        sys.exit(1)


def main_sync():
    """a sync thing to make ts work with pypi"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[bold yellow]⚠️ You hit Ctrl+C! Awwwww bye bye[/bold yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]✗ SOMETHING BROKE:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_sync()
