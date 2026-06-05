"""turning a tree into something you can save: plain text, json or csv.
finally ticking those boxes off the feature tracker :)"""
import csv
import io
import json


def to_text(node, show_stats=False):
    """the same ascii tree you see in the terminal, just as a plain string"""
    return node.generate_tree(use_color=False, show_stats=show_stats)


def to_json(node, indent=2, include_description=True):
    """nested json with all the metadata we collected"""
    data = node.to_dict(include_stats=True, include_description=include_description)
    return json.dumps(data, indent=indent, ensure_ascii=False)


def to_csv(node):
    """flat csv, one row per project. nice for spreadsheets / pandas nerds"""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "id", "title", "parent_id", "depth",
        "shared_date", "likes", "views", "favorites", "remix_count",
    ])
    for n, depth, parent_id in node.iter_nodes():
        writer.writerow([
            n.project_id,
            n.title,
            "" if parent_id is None else parent_id,
            depth,
            n.shared_date or "",
            n.likes,
            n.views,
            n.favorites,
            len(n.children),
        ])
    return out.getvalue()


# tiny helpers so callers dont have to know about file extensions
_EXPORTERS = {
    "txt": to_text,
    "json": to_json,
    "csv": to_csv,
}


def export(node, fmt="txt", show_stats=False):
    """render a tree in whatever format, fmt is one of txt/json/csv"""
    fmt = (fmt or "txt").lower()
    if fmt not in _EXPORTERS:
        raise ValueError(f"dunno how to export as {fmt!r}, pick one of {sorted(_EXPORTERS)}")
    if fmt == "txt":
        return to_text(node, show_stats=show_stats)
    return _EXPORTERS[fmt](node)


def format_from_extension(path, default="txt"):
    """guess the format from a filename, so 'tree.json' just works"""
    if not path:
        return default
    lower = path.lower()
    if lower.endswith(".json"):
        return "json"
    if lower.endswith(".csv"):
        return "csv"
    return default
