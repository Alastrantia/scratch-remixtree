import re, requests

PROJECT_ID = 1230616495

html = requests.get(f"https://scratch.mit.edu/projects/{PROJECT_ID}/remixes/").text
ids = re.findall(r"\/projects\/(\d+)\/", html)
uids = set(ids)
ids = list(uids)
print(ids)
print(len(ids))