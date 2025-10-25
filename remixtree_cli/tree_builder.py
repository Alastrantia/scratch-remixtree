from .node import RemixNodes
from .api import fetch_project_data, get_all_remixes
from rich.console import Console
import asyncio

console = Console()

async def build_remix_tree(session, project_id, project_title, max_depth=None, current_depth=0, verbose=False):
    """the **recursive** function to construct the remix tree, did i mention it is recursive already?"""
    node = RemixNodes(project_id, project_title)
    
    if max_depth is not None and current_depth >= max_depth:
        return node
    
    if verbose:
        console.print(f"{'  ' * current_depth}[dim]Checking[/dim] project [bold green]{project_id}[/bold green] (Level: {current_depth})")
    
    data = await fetch_project_data(session, project_id)
    if not data:
        return node
    
    num_remixes = data.get("stats", {}).get("remixes", 0)
    
    if num_remixes > 0:
        remixes = await get_all_remixes(session, project_id, num_remixes, verbose)
        
        child_tasks = []
        for remix in remixes:
            remix_id = remix["id"]
            remix_title = remix["title"]
            child_tasks.append(
                build_remix_tree(session, remix_id, remix_title, max_depth, current_depth + 1, verbose)
            )
        
        children = await asyncio.gather(*child_tasks)
        
        for child in children:
            node.add_child(child)
    
    return node