import aiohttp

from remixtree.api import fetch_project_data, get_root_id, get_all_remixes

API = "https://api.scratch.mit.edu"


async def test_fetch_project_data_ok(mocked):
    mocked.get(f"{API}/projects/7", payload={"id": 7, "title": "x"})
    async with aiohttp.ClientSession() as session:
        data = await fetch_project_data(session, 7)
    assert data["id"] == 7


async def test_fetch_project_data_404_is_none(mocked):
    mocked.get(f"{API}/projects/7", status=404)
    async with aiohttp.ClientSession() as session:
        assert await fetch_project_data(session, 7) is None


async def test_fetch_project_data_server_error_is_none(mocked):
    mocked.get(f"{API}/projects/7", status=503)
    async with aiohttp.ClientSession() as session:
        assert await fetch_project_data(session, 7) is None


async def test_get_root_id_follows_remix_root(mocked):
    mocked.get(f"{API}/projects/9", payload={"id": 9, "remix": {"root": 3}})
    async with aiohttp.ClientSession() as session:
        assert await get_root_id(session, 9) == 3


async def test_get_root_id_without_remix_returns_self(mocked):
    mocked.get(f"{API}/projects/9", payload={"id": 9, "remix": {"root": None}})
    async with aiohttp.ClientSession() as session:
        assert await get_root_id(session, 9) == 9


async def test_get_root_id_for_original_project(mocked):
    mocked.get(f"{API}/projects/9", payload={"id": 9})
    async with aiohttp.ClientSession() as session:
        assert await get_root_id(session, 9) == 9


async def test_get_all_remixes_single_batch(mocked):
    mocked.get(
        f"{API}/projects/5/remixes?limit=40&offset=0",
        payload=[{"id": 6, "title": "a"}, {"id": 7, "title": "b"}],
    )
    async with aiohttp.ClientSession() as session:
        out = await get_all_remixes(session, 5, 2)
    assert [r["id"] for r in out] == [6, 7]


async def test_get_all_remixes_zero_short_circuits(mocked):
    async with aiohttp.ClientSession() as session:
        assert await get_all_remixes(session, 5, 0) == []
