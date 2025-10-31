import sys
import time
import asyncio
import aiohttp
import argparse
import io

from .api import get_root_id, fetch_project_data
from .tree_builder import build_remix_tree
from .ugly_stuff import get_tree_representation
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from .cli import parse_args

# force utf8 on windows so my tests dont fail bahhhh
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# configure CLi args in cli.py
console = Console()

async def main():
    args = parse_args()
    PROJECT_ID = args.project_id
    MAX_DEPTH = args.depth
    TIMEOUT = args.timeout
    OUTPUT_FILE = args.output
    USE_COLOR = args.color
    VERBOSE = args.verbose
    
    total_children_count = 0
    
    console.print(Panel(
        f"[bold cyan]#BringBackRemixTrees (ID: {PROJECT_ID})[/bold cyan]",
        expand=False,
        border_style="cyan"
    ))
    
    timeout_config = aiohttp.ClientTimeout(total=TIMEOUT)
    connector = aiohttp.TCPConnector(limit=50) 
    
    try:
        async with aiohttp.ClientSession(timeout=timeout_config, connector=connector) as session:
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True 
            ) as progress:
                
                task1 = progress.add_task("Figuring out where the original project is...", total=None)
                root = await get_root_id(session, PROJECT_ID)
                progress.update(task1, completed=True)
                
                task2 = progress.add_task("Getting the stats for the main project...", total=None)
                root_data = await fetch_project_data(session, root)
                if not root_data:
                    console.print("[bold red]✗ Failed[/bold red] to fetch root project data")
                    sys.exit(1)
                progress.update(task2, completed=True)
                
                root_remix_count = root_data.get("stats", {}).get("remixes", 0)
            
            console.print()
            console.print(f"[bold]Start Project ID:[/bold] {PROJECT_ID}")
            console.print(f"[bold]OG Project ID:[/bold] [yellow]{root}[/yellow] (Total direct remixes: [bold]{root_remix_count}[/bold])")
            if MAX_DEPTH:
                console.print(f"[bold]We'll only go this deep (Max depth):[/bold] {MAX_DEPTH}")
            if OUTPUT_FILE:
                console.print(f"[bold]Saving the full result to:[/bold] [green]{OUTPUT_FILE}[/green]")
            if USE_COLOR:
                console.print(f"[bold]Using color mode![/bold]")
            console.print()
            
            if root_remix_count > 5000:
                console.print("[bold yellow](Pray for the Scratch Servers)[/bold yellow] This tree is huge, it's gonna take a bit. In the meantime, follow Joshisaurio on Scratch!")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task3 = progress.add_task(
                    f"[cyan]Building the tree, starting from {root}...",
                    total=None
                )
                start_time = time.perf_counter()
                tree = await build_remix_tree(session, root, "root", MAX_DEPTH, progress=progress, verbose=VERBOSE)
                end_time = time.perf_counter()
                progress.update(task3, completed=True)
            
            elapsed_time = end_time - start_time
            
            # count nodes
            def count_nodes(node):
                return 1 + sum(count_nodes(child) for child in node.children)
            
            total_children_count = count_nodes(tree)
            
            tree_output = get_tree_representation(tree, use_color=USE_COLOR)
            
            console.print()
            panel_content = (
                f"[bold green]All done! We found everything.[/bold green]\n"
                f"[cyan]Total Projects Found (Nodes):[/cyan] [bold]{total_children_count}[/bold] (Root + all the kids!)\n"
                f"[cyan]Time Taken:[/cyan] [bold]{elapsed_time:.2f} seconds[/bold]"
            )
            console.print(Panel(
                panel_content,
                expand=False,
                border_style="green"
            ))
            
            if OUTPUT_FILE:
                try:
                    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                        f.write(tree_output)
                    console.print(f"[bold green]✓ Success:[/bold green] Full tree saved to [yellow]{OUTPUT_FILE}[/yellow].")
                except Exception as e:
                    console.print(f"[bold red]✗ FILE ERROR:[/bold red] Couldn't save to {OUTPUT_FILE}: {e}")
            else:
                console.print("\n--- Tree Structure Preview ---")
                lines = tree_output.strip().split('\n')
                for i, line in enumerate(lines[:11]):
                    console.print(line, highlight=False) 
                
                if len(lines) > 11:
                    console.print("[dim]... (The rest is long! Use -o flag to save the full structure)[/dim]")
                console.print("------------------------------")
            
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