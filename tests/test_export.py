import json

import pytest

import remixtree.export as ex
from remixtree.node import RemixNodes


def make_tree():
    root = RemixNodes(1, "root [x]", likes=10, views=20, favorites=3, shared_date="2020-01-01")
    root.add_child(RemixNodes(2, "child", likes=1))
    return root


def test_to_text_has_connectors_and_no_markup():
    t = ex.to_text(make_tree())
    assert "root [x](1)" in t
    assert "child(2)" in t
    assert "└──" in t
    assert "[cyan]" not in t


def test_to_text_with_stats():
    t = ex.to_text(make_tree(), show_stats=True)
    assert "♥10" in t and "★3" in t


def test_to_json_roundtrips():
    d = json.loads(ex.to_json(make_tree()))
    assert d["id"] == 1
    assert d["likes"] == 10
    assert d["children"][0]["id"] == 2
    # to_json includes description by default
    assert "description" in d


def test_to_csv_rows():
    rows = ex.to_csv(make_tree()).strip().splitlines()
    assert rows[0].startswith("id,title,parent_id,depth")
    assert len(rows) == 3  # header + root + child
    # the child's parent_id column should be the root id
    child_cols = rows[2].split(",")
    assert child_cols[0] == "2"
    assert child_cols[2] == "1"


def test_format_from_extension():
    assert ex.format_from_extension("a.json") == "json"
    assert ex.format_from_extension("a.JSON") == "json"
    assert ex.format_from_extension("a.csv") == "csv"
    assert ex.format_from_extension("a.txt") == "txt"
    assert ex.format_from_extension(None) == "txt"


def test_export_dispatch():
    tree = make_tree()
    assert ex.export(tree, "json") == ex.to_json(tree)
    assert ex.export(tree, "csv") == ex.to_csv(tree)
    assert "└──" in ex.export(tree, "txt")


def test_export_bad_format_raises():
    with pytest.raises(ValueError):
        ex.export(make_tree(), "xml")
