"""shared test stuff. the whole point here is that NONE of these tests touch the
real scratch api, so they dont randomly break when someone unshares a project :')"""
import pytest
from aioresponses import aioresponses

API = "https://api.scratch.mit.edu"


def project_blob(pid, title=None, remixes=0, loves=0, favorites=0, views=0,
                 shared="2020-01-01T00:00:00.000Z", description="a description"):
    """fake what the scratch api hands back for a project"""
    return {
        "id": pid,
        "title": title if title is not None else f"project {pid}",
        "description": description,
        "stats": {"remixes": remixes, "loves": loves, "favorites": favorites, "views": views},
        "history": {"shared": shared},
    }


@pytest.fixture
def blob():
    return project_blob


@pytest.fixture
def mocked():
    """an active aioresponses() so tests can register fake endpoints"""
    with aioresponses() as m:
        yield m


@pytest.fixture
def register_tree(mocked):
    """register a whole fake scratch graph in one go.

    graph looks like {pid: {"children": [pids], ...project_blob kwargs}}
    """
    def _register(graph):
        for pid, spec in graph.items():
            spec = dict(spec)
            children = spec.pop("children", [])
            parent = project_blob(pid, remixes=len(children), **spec)
            mocked.get(f"{API}/projects/{pid}", payload=parent, repeat=True)
            if children:
                # the remix listing carries each child's own metadata, just like the real api
                listing = []
                for c in children:
                    cspec = dict(graph.get(c, {}))
                    cchildren = cspec.pop("children", [])
                    listing.append(project_blob(c, remixes=len(cchildren), **cspec))
                mocked.get(
                    f"{API}/projects/{pid}/remixes?limit=40&offset=0",
                    payload=listing, repeat=True,
                )
        return mocked
    return _register
