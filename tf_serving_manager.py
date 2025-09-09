import os, socket, time, json, requests, docker
from pathlib import Path


LABEL_KEY = "project"
LABEL_VAL = "ModelServerREST"
REGISTRY = Path(".tfserving_registry.json")

client = docker.from_env()


def _get_free_port(start=8501, end=8999):
    for port in range(start, end+1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free port available in range.")


def _load_registry():
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {}

def _save_registry(data):
    REGISTRY.write_text(json.dumps(data, indent=2), encoding="utf-8")

def _container_name(model_name):
    return f"tf_{model_name}"


# Starts container or returns already existing one
def ensure_container(model_name: str, model_abs_path: str, timeout=60):
    registry = _load_registry()

    # Is there already a container in the registry?
    if model_name in registry:
        info = registry[model_name]
        # container still running?
        try:
            c = client.containers.get(info["container_name"])
            if c.status in ("running", "created"):
                return info  # reuse
        except docker.errors.NotFound:
            pass  

    # If there's an old container with the same name, clean it
    try:
        old = client.containers.get(_container_name(model_name))
        old.remove(force=True)
    except docker.errors.NotFound:
        pass

    host_port = _get_free_port()
    print("Found free port:", host_port)

    # Mount the model folder as read-only
    volumes = {
        model_abs_path: {"bind": f"/models/{model_name}", "mode": "ro"}
    }

    container = client.containers.run(
        image="tensorflow/serving:latest",
        name=_container_name(model_name),
        detach=True,
        environment={"MODEL_NAME": model_name},
        volumes=volumes,
        ports={"8501/tcp": host_port},  # REST
        labels={LABEL_KEY: LABEL_VAL, "model_name": model_name},
        command=f"--model_base_path=/models/{model_name} --rest_api_port=8501 --port=8500"
    )

    # Wait for ready state
    status_url = f"http://localhost:{host_port}/v1/models/{model_name}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(status_url, timeout=2)
            if r.ok and "model_version_status" in r.json():
                states = r.json()["model_version_status"]
                if any(s.get("state") == "AVAILABLE" for s in states):
                    info = {
                        "container_name": container.name,
                        "host_port": host_port,
                        "serving_url": f"http://localhost:{host_port}/v1/models/{model_name}:predict",
                        "status_url": status_url,
                        "model_name": model_name,
                    }
                    registry[model_name] = info
                    _save_registry(registry)
                    return info
        except requests.RequestException:
            pass
        time.sleep(1)

    # If not available, clean and throw error
    container.remove(force=True)
    raise RuntimeError(f"TF Serving for '{model_name}' did not become AVAILABLE in {timeout}s.")


def stop_container(model_name: str):
    registry = _load_registry()
    try:
        c = client.containers.get(_container_name(model_name))
        c.remove(force=True)
    except docker.errors.NotFound:
        pass
    if model_name in registry:
        del registry[model_name]
        _save_registry(registry)


def list_managed_containers():
    return client.containers.list(
        all=True,
        filters={"label": f"{LABEL_KEY}={LABEL_VAL}"}
    )