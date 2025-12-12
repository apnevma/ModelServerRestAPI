import requests
from requests.auth import HTTPBasicAuth
import os
from urllib.parse import quote
import logging

HARBOR_URL = os.getenv("HARBOR_URL", "https://harbor.modul4r.rid-intrasoft.eu")
HARBOR_PROJECT = os.getenv("HARBOR_PROJECT", "intra_swarmlearning")
HARBOR_USERNAME = os.getenv("HARBOR_USERNAME")
HARBOR_PASSWORD = os.getenv("HARBOR_PASSWORD")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

AUTH = HTTPBasicAuth(HARBOR_USERNAME, HARBOR_PASSWORD) if HARBOR_USERNAME else None
TIMEOUT = 15  # seconds

def _get_repos(page=1, page_size=100):
    url = f"{HARBOR_URL.rstrip('/')}/api/v2.0/projects/{quote(HARBOR_PROJECT, safe='')}/repositories"
    params = {"page": page, "page_size": page_size}
    r = requests.get(url, auth=AUTH, timeout=TIMEOUT, params=params)
    r.raise_for_status()
    return r.json()


def _get_artifacts_for_repo(repo_name, page=1, page_size=100):
    url = f"{HARBOR_URL.rstrip('/')}/api/v2.0/projects/{quote(HARBOR_PROJECT, safe='')}/repositories/{quote(repo_name, safe='')}/artifacts"
    params = {"page": page, "page_size": page_size}
    r = requests.get(url, auth=AUTH, timeout=TIMEOUT, params=params)
    r.raise_for_status()
    return r.json()


def list_harbor_models():
    """Return flattened list of available model candidates from Harbor.
    Each entry: { source:'harbor', model_name, repo, tag, identifier, image }
    """
    
    models = []
    page = 1
    while True:
        repos = _get_repos(page=page)
        logging.info(f"[HARBOR_CLIENT] HARBOR RAW REPOS: {repos}")
        if not repos:
            break
        for repo in repos:
            full_name = repo.get("name")    # e.g. "intra_swarmlearning/saved_model"

            # Strip "<project>/" prefix →
            if full_name.startswith(f"{HARBOR_PROJECT}/"):
                repo_name = full_name[len(HARBOR_PROJECT) + 1:]
            else:
                repo_name = full_name

            # artifacts (tags) for the repo
            a_page = 1
            while True:
                artifacts = _get_artifacts_for_repo(repo_name, page=a_page)
                if not artifacts:
                    break
                for artifact in artifacts:
                    tags = artifact.get("tags") or []
                    for tag in tags:
                        tag_name = tag.get("name")
                        identifier = f"{repo_name}:{tag_name}"
                        models.append({
                            "source": "harbor",
                            "model_name": repo_name.split("/")[-1],
                            "repo": repo_name,
                            "tag": tag_name,
                            "identifier": identifier,   # use this when downloading
                            "image": f"{HARBOR_URL.rstrip('/')}/{full_name}:{tag_name}"
                        })
                a_page += 1
        page += 1

    return models
    

"""
def list_harbor_models():
    url = f"{HARBOR_URL}/api/v2.0/projects/{HARBOR_PROJECT}/repositories"
    resp = requests.get(url, auth=HTTPBasicAuth(HARBOR_USERNAME, HARBOR_PASSWORD))
    resp.raise_for_status()

    repos = resp.json()

    models = []

    for repo in repos:
        repo_name = repo["name"]    # e.g. "models/fire_nn"
        tags_url = f"{HARBOR_URL}/api/v2.0/projects/{HARBOR_PROJECT}/repositories/{repo_name}/artifacts"
        tags_resp = requests.get(tags_url, auth=HTTPBasicAuth(HARBOR_USERNAME, HARBOR_PASSWORD))
        tags_resp.raise_for_status()

        for artifact in tags_resp.json():
            tag_list = artifact.get("tags", [])
            for tag in tag_list:
                models.append({
                    "model_name": repo_name.split("/")[-1],
                    "tag": tag["name"],
                    "image": f"{HARBOR_URL}/{repo_name}:{tag['name']}"
                })

    return models

"""