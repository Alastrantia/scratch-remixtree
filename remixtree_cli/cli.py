import argparse

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