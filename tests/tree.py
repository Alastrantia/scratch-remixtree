import sys
import time

import requests
from node import *

if len(sys.argv) == 1:
    print("usage: python script.py <PROJECT_ID>")
    sys.exit(1)

PROJECT_ID = sys.argv[1]
total_children_count = 0


def fetch_project_data(extended_url, base_url="https://api.scratch.mit.edu/projects/"):
    try:
        response = requests.get(f"{base_url}{extended_url}")
        if response.status_code != 200:
            if response.status_code == 404:
                print(
                    "Got 404, perhaps the project you're trying to access is not there?"
                )
                sys.exit(1)
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
            start_time = time.perf_counter()
            response = requests.get(
                f"https://api.scratch.mit.edu/projects/{project_id}/remixes?limit=40&offset={index}"
            )
            end_time = time.perf_counter()
            print(
                f"getting remixes for {project_id}, took {(end_time - start_time):.4f} seconds"
            )
            all_remixes += response.json()

    except Exception as e:
        print(f"oop, something went wrong when getting the remixes... {e}")
    return all_remixes


# i feel like a god this is the first time ive ever used recursive funcs :sob:
def build_remix_tree(project_id, max_depth=None, current_depth=0):
    global total_children_count
    node = RemixNodes(project_id)
    if max_depth != None and current_depth >= max_depth:
        return node

    num_remixes = get_num_remixes(project_id)

    if num_remixes > 0:
        all_remixes = get_all_remixes(project_id, num_remixes)

        for remix in all_remixes:
            remix_id = remix["id"]
            total_children_count += 1
            child_node = build_remix_tree(remix_id, max_depth, current_depth + 1)
            node.add_child(child_node)

    return node


def main():
    root = get_root_id(PROJECT_ID)
    root_remix_count = get_num_remixes(root)
    if root_remix_count > 5000:
        print("sorry bud this would take forever and kill the scratch servers on the way...")
        sys.exit(0)

    print(f"the project initially came from {root}")
    print(f"that 'root' has {root_remix_count} DIRECT remixes")
    print(f"making tree from {root}...")

    start_time = time.perf_counter()
    tree = build_remix_tree(root)
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print(f"done hehe, in total we have {total_children_count} projects :O")
    tree.print_tree()
    print(f"building the tree took {elapsed_time:.4f} seconds.")


main()