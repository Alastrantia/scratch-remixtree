import requests
from node import *

PROJECT_ID = 948573479

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
            data = response.json()
            print(f"got {response.status_code}: len: {len(data)}, index: {index}")
            
            all_remixes += data

        print("fetched remixes sucessfully i guess")
    except Exception as e:
        print(f"oop, something went wrong when getting the remixes... {e}")
    return all_remixes


def main():
    root = get_root_id(PROJECT_ID)
    root_count = get_num_remixes(root)

    print(f"the root of {PROJECT_ID} ({root}) has {root_count} remixes")
    get_all_remixes(root, root_count)


main()
