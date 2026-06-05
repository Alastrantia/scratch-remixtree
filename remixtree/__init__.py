from .tree_builder import build_remix_tree
from .node import RemixNodes, extract_metadata
from .api import get_root_id, fetch_project_data
from .export import to_text, to_json, to_csv
import aiohttp
import asyncio

async def build_tree_async(project_id, max_depth=None, timeout=300, progress_callback=None):
    """async function to get tree without CLI integration"""
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_config) as session:
        root = await get_root_id(session, project_id)
        root_data = await fetch_project_data(session, root)
        if not root_data:
            raise RuntimeError(f"couldn't fetch root project {root}")
        # used to copy-paste the metadata extraction here too, extract_metadata fixed that
        tree = await build_remix_tree(session, root, root_data.get("title"), max_depth, progress=None, verbose=False, on_node_completed=progress_callback, **extract_metadata(root_data))
        return tree

def build_tree(project_id, max_depth=None, timeout=300, progress_callback=None):
    """sync wrapper"""
    return asyncio.run(build_tree_async(project_id, max_depth, timeout=timeout, progress_callback=progress_callback))

__all__ = ['build_tree', 'build_tree_async', 'RemixNodes', 'to_text', 'to_json', 'to_csv']
