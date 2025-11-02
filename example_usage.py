import remixtree

PROJECT_ID = 1190759830

"""This is supposed to be a small example on how to use the functions externally with a progress callback"""
"""This has nothing to do with the CLI functionality, we're using it as a module"""

# that's the callback function that will be called by build_tree every time a node is completed
async def node_completed(node, depth, status):
    print(f"Completed: {node.title} (ID: {node.project_id}, Depth: {depth}, Children: {len(node.children)})")
    
# tree will be a RemixNodes object, you can see its methods/attributes in node.py   
tree = remixtree.build_tree(PROJECT_ID, progress_callback=node_completed)
# this outputs the RemixNodes object as plaintext with unicode characters as in the CLI
tree.generate_tree()