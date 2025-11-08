from .tree_builder import build_remix_tree
from .node import RemixNodes
from .api import get_root_id, fetch_project_data
import aiohttp
import asyncio

async def build_tree_async(project_id, max_depth=None, timeout=300, progress_callback=None):
    """async function to get tree without CLI integration"""
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_config) as session:
        root = await get_root_id(session, project_id)
        root_data = await fetch_project_data(session, root)
        root_title = root_data["title"]
        root_shared = root_data.get("history", {}).get("shared")
        root_likes = root_data.get("stats", {}).get("loves")
        root_favorites = root_data.get("stats", {}).get("favorites")
        root_views = root_data.get("stats", {}).get("views")
        root_description = root_data["description"]
        # its getting repetitive, i have this data extraction in 3 locations...
        # but idk how to make this DRY
        
        tree = await build_remix_tree(session, root, root_title, max_depth, progress=None, verbose=False, on_node_completed=progress_callback, shared_date=root_shared, likes=root_likes, favorites=root_favorites, views=root_views, description=root_description)
        return tree

def build_tree(project_id, max_depth=None, timeout=300, progress_callback=None):
    """sync wrapper"""
    return asyncio.run(build_tree_async(project_id, max_depth, timeout=timeout, progress_callback=progress_callback))

__all__ = ['build_tree', 'build_tree_async', 'RemixNodes']