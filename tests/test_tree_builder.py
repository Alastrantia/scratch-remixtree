import aiohttp

from remixtree.tree_builder import build_remix_tree


async def test_builds_nested_tree(register_tree):
    register_tree({
        1: {"children": [2, 3], "title": "root"},
        2: {"children": [4]},
        3: {"children": []},
        4: {"children": []},
    })
    async with aiohttp.ClientSession() as session:
        tree = await build_remix_tree(session, 1, "root")

    assert tree.project_id == 1
    assert tree.count_nodes() == 4
    assert tree.max_depth() == 2
    assert sorted(c.project_id for c in tree.children) == [2, 3]
    # node 2 should own node 4
    node2 = next(c for c in tree.children if c.project_id == 2)
    assert [c.project_id for c in node2.children] == [4]


async def test_respects_max_depth(register_tree):
    register_tree({
        1: {"children": [2]},
        2: {"children": [3]},
        3: {"children": []},
    })
    async with aiohttp.ClientSession() as session:
        tree = await build_remix_tree(session, 1, "root", max_depth=1)

    # root + its direct kids only
    assert tree.count_nodes() == 2
    assert tree.max_depth() == 1


async def test_leaf_project_has_no_children(register_tree):
    register_tree({1: {"children": []}})
    async with aiohttp.ClientSession() as session:
        tree = await build_remix_tree(session, 1, "root")
    assert tree.children == []
    assert tree.count_nodes() == 1


async def test_on_node_completed_fires_for_every_node(register_tree):
    register_tree({
        1: {"children": [2, 3]},
        2: {"children": []},
        3: {"children": []},
    })
    seen = []

    async def callback(node, depth, status):
        seen.append((node.project_id, status))

    async with aiohttp.ClientSession() as session:
        await build_remix_tree(session, 1, "root", on_node_completed=callback)

    assert len(seen) == 3
    assert {pid for pid, _ in seen} == {1, 2, 3}


async def test_carries_metadata_into_nodes(register_tree):
    register_tree({
        1: {"children": [2], "title": "root", "loves": 50},
        2: {"children": [], "loves": 9, "views": 100},
    })
    async with aiohttp.ClientSession() as session:
        tree = await build_remix_tree(session, 1, "root")
    child = tree.children[0]
    assert child.likes == 9
    assert child.views == 100
