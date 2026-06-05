"""shared test stuff. the whole point here is that NONE of these tests touch the
real scratch api, so they dont randomly break when someone unshares a project :')

we fake the aiohttp session instead of patching aiohttp's guts, so this also doesnt
break every time aiohttp bumps a version (looking at you, 3.14)."""
import pytest

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


class _FakeResponse:
    """quacks like an aiohttp response for `async with session.get(...) as r`"""
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def json(self):
        return self._payload


class FakeSession:
    """stand-in for aiohttp.ClientSession. our api functions all take a session,
    so we just hand them this and skip the network entirely."""
    def __init__(self):
        self._routes = {}      # url -> (status, payload)
        self._errors = set()   # urls that should blow up like a dropped connection
        self.requested = []    # every url we got asked for, handy for assertions

    def add(self, url, payload=None, status=200):
        self._routes[url] = (status, payload)
        return self

    def add_error(self, url):
        self._errors.add(url)
        return self

    def get(self, url, **kwargs):
        self.requested.append(url)
        if url in self._errors:
            raise RuntimeError("simulated connection failure")
        status, payload = self._routes.get(url, (404, None))
        return _FakeResponse(status, payload)


@pytest.fixture
def blob():
    return project_blob


@pytest.fixture
def make_session():
    """grab an empty FakeSession and .add(url, payload[, status]) what you need"""
    return FakeSession


@pytest.fixture
def register_tree():
    """build a FakeSession wired up for a whole fake scratch graph in one go.

    graph looks like {pid: {"children": [pids], ...project_blob kwargs}}
    """
    def _register(graph):
        session = FakeSession()
        for pid, spec in graph.items():
            spec = dict(spec)
            children = spec.pop("children", [])
            session.add(f"{API}/projects/{pid}", project_blob(pid, remixes=len(children), **spec))
            if children:
                # the remix listing carries each child's own metadata, just like the real api
                listing = []
                for c in children:
                    cspec = dict(graph.get(c, {}))
                    cchildren = cspec.pop("children", [])
                    listing.append(project_blob(c, remixes=len(cchildren), **cspec))
                session.add(f"{API}/projects/{pid}/remixes?limit=40&offset=0", listing)
        return session
    return _register
