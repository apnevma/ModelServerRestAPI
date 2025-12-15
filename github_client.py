import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_REPO:
    raise RuntimeError("GITHUB_REPO is not set")

HEADERS = {
    "Accept": "application/vnd.github+json"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

TIMEOUT = 15


def test_github_access():
    url = f"https://api.github.com/repos/{GITHUB_REPO}"
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    print(r.json()["full_name"]) 


def list_repo_root():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
    params = {"ref": GITHUB_BRANCH}
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, params=params)
    r.raise_for_status()
    return r.json()


def list_github_models():
    items = list_repo_root()
    models = {}

    for item in items:
        name = item["name"]

        # Case 1: single files
        if item["type"] == "file":
            model_name = name
            models[model_name] = {
                "source": "github",
                "model_name": model_name,
                "repo_path": name
            }

        # Case 2: folder-based model
        elif item["type"] == "dir":
            model_name = name
            models[model_name] = {
                "source": "github",
                "model_name": model_name,
                "repo_path": name
            }
    print(models)
    return models
