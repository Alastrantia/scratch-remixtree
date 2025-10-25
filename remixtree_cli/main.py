import sys
import time
import asyncio
import aiohttp
import argparse
import io

from .node import RemixNodes 
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, track
from rich.panel import Panel
from datetime import timedelta
# sorry yall but i felt like putting almost everything in one file today

# force utf8 on windows cuz windows is extremely dumb it seems
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# make rich console
console = Console()
total_children_count = 0

# global var to hold runtime arguments for conditional logging
GLOBAL_ARGS = None

async def fetch_project_data(session, project_id):
    """get basic info for a scratch project"""
    url = f"https://api.scratch.mit.edu/projects/{project_id}"
    try:
        async with session.get(url) as response:
            if response.status == 404:
                console.print(f"[bold red]✗ WHOOPS (404):[/bold red] Couldn't find project {project_id}. Maybe it's gone?")
                return None
            if response.status != 200:
                console.print(f"[bold red]✗ BUMMER:[/bold red] API status {response.status} when trying to fetch data for {project_id}")
                return None
            return await response.json()
    except Exception as e:
        console.print(f"[bold red]✗ CONNECTION FAILED:[/bold red] Error fetching {url}: {e}")
        return None


async def get_root_id(session, project_id):
    """tells me where it all actually came from"""
    data = await fetch_project_data(session, project_id)
    if data and data.get("remix"):
        root_id = data["remix"].get("root")
        return root_id if root_id else project_id
    return project_id


async def fetch_remixes_batch(session, url, project_id, offset):
    """takes a batch of remixes from the scratch api, obvisously"""
    start_time = time.perf_counter()
    try:
        async with session.get(url) as response:
            end_time = time.perf_counter()
            if GLOBAL_ARGS and GLOBAL_ARGS.verbose:
                elapsed = end_time - start_time
                console.print(f"[dim]  [Batch][/dim] Got a remix chunk for {project_id} (offset {offset}), took {elapsed:.4f}s")
            
            if response.status == 200:
                return await response.json()
            return []
    except Exception as e:
        console.print(f"[bold red]✗ ERROR GETTING BATCH:[/bold red] Failed to fetch chunk for {project_id}: {e}")
        return []


async def get_all_remixes(session, project_id, num_remixes):
    """Sets up all the quick, concurrent tasks to fetch remixes for one project."""
    if num_remixes == 0:
        return []
    
    tasks = []
    # ST if you see this please make the limit per request higher than 40 uwu
    for offset in range(0, num_remixes, 40):
        url = f"https://api.scratch.mit.edu/projects/{project_id}/remixes?limit=40&offset={offset}"
        tasks.append(fetch_remixes_batch(session, url, project_id, offset))
    
    # use rich.progress.track only if it's a large number of batches and we are NOT in verbose mode
    if len(tasks) > 5 and not GLOBAL_ARGS.verbose:
         results = []
         # this local progress bar helps visualize the batch fetching inside the recursion
         for future in track(
             asyncio.as_completed(tasks), 
             total=len(tasks), 
             description=f"  [cyan]Grabbing {num_remixes} remixes for {project_id}...",
             console=console
         ):
            batch = await future
            if batch:
                results.append(batch)
    else:
        results = await asyncio.gather(*tasks)
        
    all_remixes = [remix for batch in results if batch for remix in batch]
    return all_remixes


async def build_remix_tree(session, project_id, project_title, max_depth=None, current_depth=0):
    """the **recursive** function to construct the remix tree, did i mention it is recursive already?"""
    global total_children_count
    
    node = RemixNodes(project_id, project_title)
    
    if max_depth is not None and current_depth >= max_depth:
        return node
    
    if GLOBAL_ARGS and GLOBAL_ARGS.verbose:
        console.print(f"{'  ' * current_depth}[dim]Checking[/dim] project [bold green]{project_id}[/bold green] (Level: {current_depth})")
    
    data = await fetch_project_data(session, project_id)
    if not data:
        return node
    
    num_remixes = data.get("stats", {}).get("remixes", 0)
    
    if num_remixes > 0:
        remixes = await get_all_remixes(session, project_id, num_remixes)
        
        child_tasks = []
        for remix in remixes:
            remix_id = remix["id"]
            remix_title = remix["title"]
            total_children_count += 1
            child_tasks.append(
                build_remix_tree(session, remix_id, remix_title, max_depth, current_depth + 1)
            )
        
        children = await asyncio.gather(*child_tasks)
        
        for child in children:
            node.add_child(child)
    
    return node


def get_tree_representation(tree_node, use_color=True):
    """
    a really ugly workaround that steals the stdoutput from RemixNodes.print_tree() 
    it works but it's uglyyyyyy iykyk
    """
    
    # 1. save the original stdout stream
    original_stdout = sys.stdout
    
    # 2. create a StringIO object to capture output
    captured_output = io.StringIO()
    
    try:
        # 3. redirect stdout to the StringIO object
        sys.stdout = captured_output
        
        # 4. call the method that prints to stdout WITH color parameter
        tree_node.print_tree(use_color=use_color)
        
    finally:
        # 5. restore original stdout
        sys.stdout = original_stdout
    
    # get the captured string value
    return captured_output.getvalue()


def parse_args():
    parser = argparse.ArgumentParser(
        description="a replacement for scratch's remix tree feature in the form of a CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example: remixtree 123456789 -d 3 -o tree_output.txt"
    )
    parser.add_argument(
        "project_id",
        type=int,
        help="The Scratch project ID we want to start from."
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=None,
        help="how many levels deep it should go (my personal recommendation is unlimited!1!1!!!11)."
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=300,
        help="request timeout in seconds (default is 300)."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="spam your terminal window (shows every API call, looks cool)."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="path to a file to save the actual, full tree structure (e.g., tree.txt)."
    )
    parser.add_argument(
        "-c", "--color",
        action="store_true",
        default=False,
        help="enable color coding by depth (disabled by default), will use rich color formatting"
    )
    
    return parser.parse_args()


async def main():
    global total_children_count, GLOBAL_ARGS
    
    args = parse_args()
    GLOBAL_ARGS = args # set global args for conditional logging
    PROJECT_ID = args.project_id
    MAX_DEPTH = args.depth
    TIMEOUT = args.timeout
    OUTPUT_FILE = args.output
    USE_COLOR = args.color
    
    # header
    console.print(Panel(
        f"[bold cyan]#BringBackRemixTrees (ID: {PROJECT_ID})[/bold cyan]",
        expand=False,
        border_style="cyan"
    ))
    
    timeout_config = aiohttp.ClientTimeout(total=TIMEOUT)
    connector = aiohttp.TCPConnector(limit=50) 
    
    try:
        async with aiohttp.ClientSession(timeout=timeout_config, connector=connector) as session:
            
            # **rich** Progress Bar setup for the main indeterminate tasks
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True 
            ) as progress:
                
                # 1. get Root ID
                task1 = progress.add_task("Figuring out where the original project is...", total=None)
                root = await get_root_id(session, PROJECT_ID)
                progress.update(task1, completed=True)
                
                # 2. get Root Remix Count
                task2 = progress.add_task("Getting the stats for the main project...", total=None)
                root_data = await fetch_project_data(session, root)
                if not root_data:
                    console.print("[bold red]✗ Failed[/bold red] to fetch root project data")
                    sys.exit(1)
                progress.update(task2, completed=True)
                
                root_remix_count = root_data.get("stats", {}).get("remixes", 0)
            
            # info Section 
            console.print()
            console.print(f"[bold]Starting Project ID:[/bold] {PROJECT_ID}")
            console.print(f"[bold]Original Root Project ID:[/bold] [yellow]{root}[/yellow] (Total direct remixes: [bold]{root_remix_count}[/bold])")
            if MAX_DEPTH:
                console.print(f"[bold]We'll only go this deep (Max depth):[/bold] {MAX_DEPTH}")
            if OUTPUT_FILE:
                console.print(f"[bold]Saving the full result to:[/bold] [green]{OUTPUT_FILE}[/green]")
            console.print()
            
            if root_remix_count > 5000:
                console.print("[bold yellow](Pray for the Scratch Servers)[/bold yellow] This tree is huge, it's gonna take a bit. In the meantime, follow Joshisaurio on Scratch!")
            
            # 3. build Tree (Re-entering Progress scope)
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
                tree = await build_remix_tree(session, root, "root", MAX_DEPTH)
                end_time = time.perf_counter()
                progress.update(task3, completed=True)
            
            elapsed_time = end_time - start_time
            
            # final Results
            tree_output = get_tree_representation(tree, use_color=USE_COLOR)
            
            # print Final Status Panel
            console.print()
            panel_content = (
                f"[bold green]All done! We found everything.[/bold green]\n"
                f"[cyan]Total Projects Found (Nodes):[/cyan] [bold]{total_children_count + 1}[/bold] (Root + all the kids!)\n"
                f"[cyan]Time Taken:[/cyan] [bold]{elapsed_time:.2f} seconds[/bold]"
            )
            console.print(Panel(
                panel_content,
                expand=False,
                border_style="green"
            ))
            
            # output Handling
            if OUTPUT_FILE:
                try:
                    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                        f.write(tree_output)
                    console.print(f"[bold green]✓ Success:[/bold green] Full tree saved to [yellow]{OUTPUT_FILE}[/yellow].")
                except Exception as e:
                    console.print(f"[bold red]✗ FILE ERROR:[/bold red] Couldn't save to {OUTPUT_FILE}: {e}")
            else:
                # FIX: print parts of the tree to prove it even worked
                console.print("\n--- Tree Structure Preview ---")
                
                # Print the first few lines to avoid console spam
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
