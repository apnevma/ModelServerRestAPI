import time, json, requests, docker
from pathlib import Path
import logging


LABEL_KEY = "project"
LABEL_VAL = "ModelServerREST"
REGISTRY = Path(".tfserving_registry.json")

client = docker.from_env()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def _load_registry():
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {}

def _save_registry(data):
    REGISTRY.write_text(json.dumps(data, indent=2), encoding="utf-8")

def _container_name(model_name):
    return f"tf_{model_name}"


def ensure_container(model_name: str, model_subdir: str, timeout=60):
    """
    Starts a TF Serving container for the given model if not already running.
    Uses Docker network only, no host port binding.
    """
    registry = _load_registry()

    # Reuse container if already running
    if model_name in registry:
        info = registry[model_name]
        try:
            c = client.containers.get(info["container_name"])
            if c.status in ("running", "created"):
                return info
        except docker.errors.NotFound:
            pass

    # Clean up old container if it exists
    try:
        old = client.containers.get(_container_name(model_name))
        old.remove(force=True)
    except docker.errors.NotFound:
        pass

    # Mount the same named volume that docker-compose created
    volumes = {
        "modelserverrestapi_models_data": {"bind": "/models", "mode": "rw"}
    }

    model_base_path = f"/models/{model_subdir}"  # path inside container

    # Start container on Docker network (no host port mapping)
    container = client.containers.run(
        image="tensorflow/serving:latest",
        name=_container_name(model_name),
        detach=True,
        environment={"MODEL_NAME": model_name},
        volumes=volumes,
        network="model_server_net",  # Flask can reach it via container name
        labels={
            LABEL_KEY: LABEL_VAL,
            "com.docker.compose.project": "modelserverrestapi",
            "model_name": model_name
            },
        command=f"--model_base_path={model_base_path} --rest_api_port=8501 --port=8500"
    )

    # Wait until model is available
    status_url = f"http://{container.name}:8501/v1/models/{model_name}"  # use container name
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(status_url, timeout=2)
            if r.ok and "model_version_status" in r.json():
                states = r.json()["model_version_status"]
                if any(s.get("state") == "AVAILABLE" for s in states):
                    info = {
                        "container_name": container.name,
                        "serving_url": f"http://{container.name}:8501/v1/models/{model_name}:predict",
                        "status_url": status_url,
                        "model_name": model_name,
                    }
                    registry[model_name] = info
                    _save_registry(registry)
                    return info
        except requests.RequestException:
            pass
        time.sleep(1)

    # Cleanup if not available in time
    container.remove(force=True)
    raise RuntimeError(f"TF Serving for '{model_name}' did not become AVAILABLE in {timeout}s.")


def stop_container(model_name: str):
    logging.info(f"Attempting to stop tf_serving container: {model_name}")
    registry = _load_registry()
    try:
        c = client.containers.get(_container_name(model_name))
        c.remove(force=True)
    except docker.errors.NotFound:
        pass
    if model_name in registry:
        del registry[model_name]
        _save_registry(registry)
        logging.info(f"[-] Removed tf_serving container: {model_name}")


def list_managed_containers():
    return client.containers.list(
        all=True,
        filters={"label": f"{LABEL_KEY}={LABEL_VAL}"}
    )