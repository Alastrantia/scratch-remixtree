import sys
import io


def get_tree_representation(tree_node, use_color=True):
    """
    a really ugly workaround that steals the stdoutput from RemixNodes.print_tree() 
    it works but it's uglyyyyyy iykyk
    """
    original_stdout = sys.stdout
    captured_output = io.StringIO()
    
    try:
        sys.stdout = captured_output
        tree_node.print_tree(use_color=use_color)
    finally:
        sys.stdout = original_stdout
    
    return captured_output.getvalue()