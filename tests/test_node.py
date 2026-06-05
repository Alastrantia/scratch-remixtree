from remixtree.node import RemixNodes, extract_metadata, fmt_count


def test_from_project_data_pulls_everything():
    blob = {
        "id": 5, "title": "t",
        "stats": {"loves": 4, "favorites": 2, "views": 99, "remixes": 1},
        "history": {"shared": "2021-01-01"},
        "description": "d",
    }
    n = RemixNodes.from_project_data(blob)
    assert n.project_id == 5
    assert n.likes == 4
    assert n.favorites == 2
    assert n.views == 99
    assert n.shared_date == "2021-01-01"
    assert n.description == "d"


def test_extract_metadata_survives_missing_keys():
    md = extract_metadata({"id": 1})
    assert md["likes"] == 0
    assert md["favorites"] == 0
    assert md["views"] == 0
    assert md["shared_date"] is None
    assert md["description"] == ""


def test_none_values_get_coerced():
    n = RemixNodes(1, None, likes=None, views=None, favorites=None, description=None)
    assert n.title == "Untitled"
    assert n.likes == 0 and n.views == 0 and n.favorites == 0
    assert n.description == ""


def test_count_nodes_and_max_depth():
    r = RemixNodes(1, "r")
    a = RemixNodes(2, "a")
    b = RemixNodes(3, "b")
    c = RemixNodes(4, "c")
    r.add_child(a)
    a.add_child(b)
    r.add_child(c)
    assert r.count_nodes() == 4
    assert r.max_depth() == 2
    assert RemixNodes(9, "lonely").max_depth() == 0


def test_sort_children_by_share_date_both_ways():
    r = RemixNodes(1, "r")
    r.add_child(RemixNodes(2, "old", shared_date="2019-01-01"))
    r.add_child(RemixNodes(3, "new", shared_date="2022-01-01"))

    r.sort_children_by_share_date(reverse=True)  # newest first
    assert [c.project_id for c in r.children] == [3, 2]

    r.sort_children_by_share_date(reverse=False)  # oldest first
    assert [c.project_id for c in r.children] == [2, 3]


def test_sort_is_recursive():
    r = RemixNodes(1, "r")
    a = RemixNodes(2, "a", shared_date="2020-01-01")
    a.add_child(RemixNodes(3, "old", shared_date="2019-01-01"))
    a.add_child(RemixNodes(4, "new", shared_date="2021-01-01"))
    r.add_child(a)
    r.sort_children_by_share_date(reverse=True)
    assert [c.project_id for c in a.children] == [4, 3]


def test_iter_nodes_yields_depth_and_parent():
    r = RemixNodes(1, "r")
    a = RemixNodes(2, "a")
    r.add_child(a)
    out = [(n.project_id, d, p) for n, d, p in r.iter_nodes()]
    assert out == [(1, 0, None), (2, 1, 1)]


def test_to_dict_includes_stats_not_description_by_default():
    r = RemixNodes(1, "r", likes=5, views=6, favorites=7)
    r.add_child(RemixNodes(2, "k"))
    d = r.to_dict()
    assert d["likes"] == 5 and d["views"] == 6 and d["favorites"] == 7
    assert d["remix_count"] == 1
    assert "description" not in d
    assert d["children"][0]["id"] == 2


def test_to_dict_can_include_description():
    d = RemixNodes(1, "r", description="hi").to_dict(include_description=True)
    assert d["description"] == "hi"


def test_generate_tree_plain_text():
    r = RemixNodes(1, "root")
    r.add_child(RemixNodes(2, "kid"))
    text = r.generate_tree()
    assert "root(1)" in text
    assert "└── kid(2)" in text
    # no rich markup should leak into the plain text
    assert "[cyan]" not in text


def test_fmt_count():
    assert fmt_count(999) == "999"
    assert fmt_count(1500) == "1.5k"
    assert fmt_count(2_000_000) == "2.0M"
    assert fmt_count(None) == "0"
    assert fmt_count("nope") == "0"
