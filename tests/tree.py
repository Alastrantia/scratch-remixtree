import requests, sys
from node import *

PROJECT_ID = sys.argv[1]

def fetch_project_data(extended_url, base_url="https://api.scratch.mit.edu/projects/"):
    try:
        response = requests.get(f"{base_url}{extended_url}")
        if response.status_code != 200:
            print(f"Getting Root ID failed with status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching {base_url}{extended_url}: {e}")
    return response.json()


def get_root_id(project_id):
    response = fetch_project_data(f"{project_id}")
    ID = response["remix"]["root"]
    if ID == None:
        ID = project_id
    return ID


def get_num_remixes(project_id):
    response = fetch_project_data(f"{project_id}")
    count = response["stats"]["remixes"]
    return count


def get_all_remixes(project_id, num_remixes):    
    all_remixes = []

    try:
        for index in range(0, num_remixes, 40):
            response = requests.get(
                f"https://api.scratch.mit.edu/projects/{project_id}/remixes?limit=40&offset={index}"
            )
            all_remixes += response.json()

        print(".")
    except Exception as e:
        print(f"oop, something went wrong when getting the remixes... {e}")
    return all_remixes


# i feel like a god this is the first time ive ever used recursive funcs :sob:
def build_remix_tree(project_id, max_depth=None, current_depth=0):
    node = RemixNodes(project_id)
    if max_depth != None and current_depth >= max_depth:
        return node 
    
    num_remixes = get_num_remixes(project_id)
    
    if num_remixes > 0:
        all_remixes = get_all_remixes(project_id, num_remixes)

        for remix in all_remixes:
            remix_id = remix["id"]
            child_node = build_remix_tree(remix_id, max_depth, current_depth + 1)
            node.add_child(child_node)
    
    return node


def main():
    root = get_root_id(PROJECT_ID)
    root_remix_count = get_num_remixes(root)
    print(f"{root} has ")
    print(f"making tree from {root}...")
    
    # HAHAHHAHAHAHHAHAHAHAHHAHAHAA
    tree = build_remix_tree(root)
    
    print(f"done hehe")
    tree.print_tree()

main()
