import argparse

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="remixtree",
        description="a replacement for scratch's remix tree feature in the form of a CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  remixtree 123456789 -d 3 -o tree_output.txt\n"
            "  remixtree 123456789 --stats            (show loves/views/faves)\n"
            "  remixtree 123456789 -o tree.json       (format guessed from the extension)\n"
            "  remixtree 111 222 333 -o tree.csv      (batch, saves tree_111.csv, tree_222.csv, ...)"
        )
    )
    parser.add_argument(
        "project_ids",
        type=int,
        nargs="+",
        metavar="project_id",
        help="one or more Scratch project IDs we want to start from."
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
        help="path to a file to save the actual, full tree structure (e.g., tree.txt / tree.json / tree.csv)."
    )
    parser.add_argument(
        "-f", "--format",
        choices=["txt", "json", "csv"],
        default=None,
        help="what to save as. if you skip it i'll guess from the -o file extension, otherwise plain txt."
    )
    parser.add_argument(
        "-s", "--stats",
        action="store_true",
        help="show loves/views/faves next to each project (the api hands them over anyway)."
    )
    parser.add_argument(
        "-c", "--color",
        action="store_true",
        default=False,
        help="enable color coding by depth (disabled by default), will use rich color formatting"
    )

    return parser.parse_args(argv)
