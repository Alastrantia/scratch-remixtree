from .node import RemixNodes
from .api import fetch_project_data, get_all_remixes
from rich.console import Console
import asyncio

console = Console()

async def build_remix_tree(session, project_id, project_title, max_depth=None, current_depth=0, progress=None, verbose=False, on_node_completed=None, shared_date=None, likes=0, favorites=0, views=0, description=""):
    """the **recursive** function to construct the remix tree, did i mention it is recursive already?"""
    node = RemixNodes(project_id, project_title, shared_date=shared_date, likes=likes, favorites=favorites, description=description, views=views)
    
    if max_depth is not None and current_depth >= max_depth:
        if on_node_completed:
            await on_node_completed(node, current_depth, "max_depth_reached")
        return node
    
    if verbose and progress:
        progress.console.print(f"{'  ' * current_depth}[dim]Checking[/dim] project [bold green]{project_id}[/bold green] (Level: {current_depth})")
    elif verbose:
        console.print(f"{'  ' * current_depth}[dim]Checking[/dim] project [bold green]{project_id}[/bold green] (Level: {current_depth})")
    
    data = await fetch_project_data(session, project_id)
    if not data:
        if on_node_completed:
            await on_node_completed(node, current_depth, "no_data")
        return node
    
    num_remixes = data.get("stats", {}).get("remixes", 0)
    
    if num_remixes > 0:
        remixes = await get_all_remixes(session, project_id, num_remixes, progress=progress, verbose=verbose)
        
        child_tasks = []
        for remix in remixes:
            remix_id = remix["id"]
            remix_title = remix["title"]
            remix_shared = remix.get("history", {}).get("shared")
            remix_likes = remix.get("stats", {}).get("loves")
            remix_favorites = remix.get("stats", {}).get("favorites")
            remix_views = remix.get("stats", {}).get("views")
            remix_description = remix["description"]
            child_tasks.append(
                build_remix_tree(session, remix_id, remix_title, max_depth, current_depth + 1, progress=progress, verbose=verbose, on_node_completed=on_node_completed, shared_date=remix_shared, likes=remix_likes, favorites=remix_favorites, description=remix_description, views=remix_views)
            )
        
        children = await asyncio.gather(*child_tasks)
        
        for child in children:
            node.add_child(child)
        
    if on_node_completed:
        await on_node_completed(node, current_depth, "completed")
    
    return node