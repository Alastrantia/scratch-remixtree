# experiments

old throwaway scripts from when i was figuring this whole thing out. they are NOT
part of the actual test suite (pytest ignores them), just keeping them around for
nostalgia / reference.

- `old_sync_tree.py` — the original synchronous version of the tree builder, before
  everything went async and got packaged up. it imports `api.node` which doesnt even
  exist anymore, so dont expect it to run lol.
- `html_parse/main.py` — me poking at scraping remix ids straight out of the scratch
  project page html instead of using the api.

the real tests live one folder up in `tests/test_*.py` and dont touch the network.
