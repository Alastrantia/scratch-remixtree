from remixtree.api import fetch_project_data, get_root_id, get_all_remixes

API = "https://api.scratch.mit.edu"


async def test_fetch_project_data_ok(make_session):
    session = make_session()
    session.add(f"{API}/projects/7", {"id": 7, "title": "x"})
    data = await fetch_project_data(session, 7)
    assert data["id"] == 7


async def test_fetch_project_data_404_is_none(make_session):
    session = make_session()
    session.add(f"{API}/projects/7", status=404)
    assert await fetch_project_data(session, 7) is None


async def test_fetch_project_data_server_error_is_none(make_session):
    session = make_session()
    session.add(f"{API}/projects/7", status=503)
    assert await fetch_project_data(session, 7) is None


async def test_fetch_project_data_connection_error_is_none(make_session):
    session = make_session()
    session.add_error(f"{API}/projects/7")
    assert await fetch_project_data(session, 7) is None


async def test_get_root_id_follows_remix_root(make_session):
    session = make_session()
    session.add(f"{API}/projects/9", {"id": 9, "remix": {"root": 3}})
    assert await get_root_id(session, 9) == 3


async def test_get_root_id_without_remix_returns_self(make_session):
    session = make_session()
    session.add(f"{API}/projects/9", {"id": 9, "remix": {"root": None}})
    assert await get_root_id(session, 9) == 9


async def test_get_root_id_for_original_project(make_session):
    session = make_session()
    session.add(f"{API}/projects/9", {"id": 9})
    assert await get_root_id(session, 9) == 9


async def test_get_all_remixes_single_batch(make_session):
    session = make_session()
    session.add(
        f"{API}/projects/5/remixes?limit=40&offset=0",
        [{"id": 6, "title": "a"}, {"id": 7, "title": "b"}],
    )
    out = await get_all_remixes(session, 5, 2)
    assert [r["id"] for r in out] == [6, 7]


async def test_get_all_remixes_zero_short_circuits(make_session):
    session = make_session()
    out = await get_all_remixes(session, 5, 0)
    assert out == []
    # short-circuit means we never even hit the api
    assert session.requested == []
