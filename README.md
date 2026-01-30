# ML Models Serving Tool

A Flask-based REST API for **dynamic machine learning model serving** with support for Scikit-learn, TensorFlow/Keras, TensorFlow SavedModels, and PyTorch. The system provides flexible deployment options with automatic model discovery, lifecycle management, and real-time synchronization.

## Table of Contents
- [Features](#features)
- [Operating Modes](#operating-modes)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [GitHub Webhook Integration](#github-webhook-integration)
- [Event-Driven Integration](#event-driven-integration)
- [Testing](#testing)

## Features

### Core Capabilities
- **Dynamic model serving** - Automatically discovers and serves models without requiring restarts
- **Multi-framework support** - Works with Scikit-learn (`.pkl`, `.joblib`), TensorFlow/Keras (`.h5`), TensorFlow SavedModels, and PyTorch models
- **Flexible deployment** - Choose between GitHub-based or local filesystem model storage
- **Model lifecycle management** - Explicit activation/deactivation control for efficient resource usage
- **TensorFlow Serving integration** - Automatic containerized deployment for TF SavedModels
- **Real-time synchronization** - Automatic updates via GitHub webhooks or filesystem monitoring
- **Event-driven architecture** - Kafka and MQTT integration for seamless data pipeline integration
- **Web-based UI** - Interactive interface for exploring available models and endpoints
- **Thread-safe operations** - Concurrent request handling with safe state management

### Model Management
- **On-demand loading** - Models are downloaded and loaded only when activated
- **Automatic endpoint creation** - Each active model gets its own prediction endpoint
- **Model introspection** - Provides input shape and data type information for debugging
- **Graceful error handling** - Returns expected input format when predictions fail
- **File stability checks** - Prevents loading incomplete model files

## Operating Modes

The system operates in two distinct modes, controlled by the `MODEL_SOURCE` environment variable:

### 1. GitHub Mode (`MODEL_SOURCE=github`)

In this mode, the API uses a GitHub repository as a remote model registry with automatic synchronization.

**How it works:**
1. API scans the `models/` folder in the specified GitHub repository
2. All detected models are registered as **available** (but inactive)
3. When a model is activated via API, it's downloaded to `/models` and loaded
4. GitHub webhooks automatically sync model changes (additions, updates, deletions)
5. Active models are deactivated when their source files are updated or removed


**Webhook behavior:**
- **Model added**: Registered as available (requires manual activation)
- **Model modified**: Automatically deactivated if active (requires re-activation)
- **Model deleted**: Automatically deactivated and removed from registry

### 2. Local Filesystem Mode (`MODEL_SOURCE=local_filesystem`)

In this mode, the API serves models from a local directory with real-time filesystem monitoring.

**How it works:**
1. On startup, API scans the local `models/` folder
2. All detected models are registered as **available** (but inactive)
3. Filesystem watcher detects changes in real-time
4. Models can be activated without downloading


## Architecture

The system is built with a modular, maintainable architecture:

```
┌─────────────────┐
│   Flask API     │ ← HTTP endpoints for model management & predictions
└────────┬────────┘
         │
    ┌────┴────┐
    │ Registry │ ← Centralized thread-safe state management
    └────┬────┘
         │
    ┌────┴────────────────────────┐
    │                             │
┌───┴────────┐          ┌────────┴─────┐
│ Lifecycle  │          │ Sync Handler │ ← Unified change processing
│ Manager    │          └──────┬───────┘
└────────────┘                 │
                     ┌─────────┴──────────┐
                     │                    │
              ┌──────┴────────┐    ┌─────┴────────┐
              │ GitHub Webhook│    │  Filesystem  │
              │   Handler     │    │   Watcher    │
              └───────────────┘    └──────────────┘
```

### Key Components

- **model_registry.py** - Thread-safe state management for available and active models
- **model_lifecycle.py** - Handles model activation, deactivation, and cleanup
- **sync_handlers.py** - Unified logic for processing model changes from any source
- **webhook_handler.py** - Processes GitHub webhook events for model synchronization
- **filesystem_watcher.py** - Monitors local directory for model changes
- **RestAPI.py** - Flask application with prediction and management endpoints

## Installation

### Prerequisites

- Docker and Docker Compose
- Git (for GitHub mode)

### Setup

1. **Clone the repository:**
```bash
git clone <repo_url>
cd ModelServerRestAPI
```

2. **Create Docker network:**
```bash
docker network create model_server_net
```

3. **Configure environment variables:**

Create a `.env` file in the project root:

```bash
# API Configuration
PORT=8086
API_HOST=0.0.0.0
MODELS_PATH=/models

# Model Source Configuration
MODEL_SOURCE=github                    # or "local_filesystem"
GITHUB_REPO=your-org/ml-models
GITHUB_BRANCH=main
GITHUB_TOKEN=ghp_your_token_here       # Optional for public repos

```

4. **Prepare your models:**

For **local filesystem mode**, create a `models/` directory and add your models:
```
models/
│
├── rf_model.pkl                 # Scikit-learn model
├── keras_model.h5               # Keras model
├── fire_savedmodel/             # TensorFlow SavedModel
│   └── 1/
│       └── saved_model.pb
└── fire_pytorch/                # PyTorch model
    ├── model.pt
    └── model_class.py
```

For **GitHub mode**, ensure your repository has a `models/` folder with the same structure.

5. **Build and start containers:**
```bash
docker-compose up -d --build
```

The API will be available at `http://localhost:8086`

## Configuration

Configure the system using environment variables:

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_SOURCE` | `local_filesystem` | Model source: `github` or `local_filesystem` |
| `MODELS_PATH` | `/models` | Local directory for model storage |
| `API_HOST` | `localhost` | Host address for the API server |
| `PORT` | `8086` | Port for the API server |

### GitHub Mode Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REPO` | `apnevma/models-to-test` | GitHub repository (format: `owner/repo`) |
| `GITHUB_TOKEN` | - | GitHub personal access token (for private repos) |

### Messaging Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `INPUT_DATA_SOURCE` | `kafka` | Input source: `kafka` or `mqtt` |
| `PREDICTION_DESTINATION` | `kafka` | Output destination: `kafka` or `mqtt` |
| `KAFKA_OUTPUT_TOPIC` | `INTRA_test_topic1` | Kafka topic for predictions |

### Example Configuration

**Local filesystem mode:**
```bash
export MODEL_SOURCE=local_filesystem
export MODELS_PATH=/path/to/models
export PORT=8086
```

**GitHub mode:**
```bash
export MODEL_SOURCE=github
export GITHUB_REPO=your-org/ml-models
export GITHUB_TOKEN=ghp_your_token_here
export PORT=8086
```

## Usage

### Starting the Server

**GitHub mode:**
```bash
docker-compose up -d --build
```

**Local filesystem mode:**
```bash
docker-compose --profile local_filesystem up -d --build
```

The API will be available at `http://localhost:8086`

### Managing Models

#### 1. List all available models
```bash
curl http://localhost:8086/models
```

Response:
```json
[
  {
    "model_name": "rf_model",
    "status": "inactive",
    "model_path": "/models/rf_model.pkl",
    "predict_url": null
  },
  {
    "model_name": "fire_nn",
    "status": "active",
    "model_path": "/models/fire_nn.h5",
    "predict_url": "http://localhost:8086/predict/fire_nn"
  }
]
```

#### 2. Check model status
```bash
curl http://localhost:8086/status/rf_model
```

#### 3. Activate a model
```bash
curl -X POST http://localhost:8086/activate/rf_model
```

Response:
```json
{
  "message": "Model rf_model activated",
  "predict_endpoint": "/predict/rf_model"
}
```

#### 4. Deactivate a model
```bash
curl -X POST http://localhost:8086/deactivate/rf_model
```

#### 5. Make a prediction
```bash
curl -X POST http://localhost:8086/predict/fire_nn \
  -H "Content-Type: application/json" \
  -d '{"input": [[70.5, 20.0, 76.0]]}'
```

Response:
```json
{
  "status": "sent",
  "destination": "kafka",
  "prediction": [[0.85, 0.15]]
}
```

### Web Interface

Access the interactive help page at `http://localhost:8086/help/ui`

Features:
- Browse all available models
- View model endpoints and metadata
- Flip-card design with clean, modern UI
- Real-time status indicators

## API Reference

### Model Management Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/models` | GET | List all available models with status |
| `/status/<model_name>` | GET | Get status of a specific model |
| `/activate/<model_name>` | POST | Activate a model for serving |
| `/deactivate/<model_name>` | POST | Deactivate an active model |

### Prediction Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict/<model_name>` | POST | Make predictions with an active model |

**Request format:**
```json
{
  "input": [[feature1, feature2, ...]]
}
```

### Information Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/test` | GET | Health check endpoint |
| `/help` | GET | JSON documentation of active models |
| `/help/ui` | GET | Web-based interactive help page |

### Webhook Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/github/webhook` | POST | GitHub webhook receiver for model sync |

## GitHub Webhook Integration

Webhooks enable automatic synchronization when models are pushed to your GitHub repository.

### Setup Instructions

#### 1. Configure GitHub Webhook

In your GitHub repository:

1. Go to **Settings** → **Webhooks** → **Add webhook**
2. Configure the webhook:
   - **Payload URL**: `http://your-server:8086/github/webhook`
   - **Content type**: `application/json`
   - **Secret**: (optional but recommended - add signature verification)
   - **Events**: Select "Just the push event"
3. Click **Add webhook**

#### 2. Expose Your Endpoint (if testing locally)

If running locally, use a tunnel service like ngrok:

```bash
ngrok http 8086
```

Then use the ngrok URL as your webhook payload URL:
```
https://abc123.ngrok.io/github/webhook
```

#### 3. Test the Webhook

Push a model to your repository:
```bash
# Add a new model
git add models/new_model.pkl
git commit -m "Add new_model"
git push origin main
```

Check the logs:
```bash
docker logs model_server_api
```

You should see:
```
[WEBHOOK] Push received
[WEBHOOK] Model changes detected: {'added': {'new_model'}, 'removed': set(), 'modified': set()}
[SYNC] Model added: new_model
[REGISTRY] Registered model 'new_model'
```

### Webhook Behavior

The webhook handler processes different types of model changes:

**Model Added:**
- Model is registered as available
- Status: inactive (requires activation via API)
- Ready for use immediately after activation

**Model Modified:**
- Metadata is refreshed from GitHub
- If model is active, it's automatically deactivated
- Requires re-activation to load the updated version

**Model Deleted:**
- Model is deactivated if active
- Removed from available models registry
- Local files are cleaned up

### Security Considerations

For production deployments:

1. **Use HTTPS** - Configure SSL/TLS for your API server
2. **Verify webhook signatures** - Validate requests are from GitHub
3. **Restrict branches** - Only process pushes to specific branches (default: `main`)
4. **Rate limiting** - Implement rate limits on the webhook endpoint
5. **Authentication** - Use GitHub tokens for private repositories

### Troubleshooting Webhooks

**Webhook not triggering:**
- Check GitHub webhook delivery status (Settings → Webhooks → Recent Deliveries)
- Verify the payload URL is accessible from the internet
- Check firewall and network settings

**Models not updating:**
- Check logs for `[WEBHOOK]` and `[SYNC]` messages
- Verify the repository structure matches expected format
- Ensure `MODEL_SOURCE=github` is set

**Permission errors:**
- Verify GitHub token has repository read access
- Check file permissions in `/models` directory

## Event-Driven Integration

The system integrates seamlessly with event-driven architectures via Kafka and MQTT.

### Workflow

```
┌──────────┐      ┌─────────────────┐      ┌──────────┐
│  Kafka/  │─────→│  ML Serving     │─────→│  Kafka/  │
│  MQTT    │      │  Tool           │      │  MQTT    │
│ (Input)  │      │  (Prediction)   │      │ (Output) │
└──────────┘      └─────────────────┘      └──────────┘
```

### Kafka Configuration

**Input consumer:**
```bash
export INPUT_DATA_SOURCE=kafka
export KAFKA_INPUT_TOPIC=ml_input_data
export KAFKA_SERVERS=<kafka_server_ip>
```

**Output producer:**
```bash
export PREDICTION_DESTINATION=kafka
export KAFKA_OUTPUT_TOPIC=ml_predictions
```

### MQTT Configuration

**Input subscriber:**
```bash
export INPUT_DATA_SOURCE=mqtt
export MQTT_BROKER=<mqtt_broker>
export MQTT_PORT=<mqtt_port>
export MQTT_INPUT_TOPIC=ml/input
```

**Output publisher:**
```bash
export PREDICTION_DESTINATION=mqtt
export MQTT_OUTPUT_TOPIC=ml/predictions
```

### Message Format

**Input message:**
```json
{
  "model_name": "fire_nn",
  "input": [[70.5, 20.0, 76.0]]
}
```

**Output message (success):**
```json
{
  "model": "fire_nn",
  "status": "success",
  "prediction": [[0.85, 0.15]],
  "timestamp": "2026-01-30T12:34:56Z"
}
```

**Output message (error):**
```json
{
  "model": "fire_nn",
  "status": "error",
  "error": "Input shape mismatch",
  "expected_input": {"shape": [3], "type": "float32"}
}
```

## Testing

### Manual Testing with cURL

Test a prediction endpoint:
```bash
curl -X POST http://localhost:8086/predict/fire_nn \
  -H "Content-Type: application/json" \
  -d '{"input": [[70.5, 20.0, 76.0]]}'
```

### Python Testing Script

Use the provided test script:

```python
import requests

# Configuration
url = "http://localhost:8086/predict/fire_nn"
data = {
    "input": [[70.5, 20.0, 76.0]]
}

try:
    response = requests.post(url, json=data)
    response.raise_for_status()
    
    prediction = response.json()
    print("Prediction:", prediction)
    
except requests.exceptions.RequestException as e:
    print("Error:", e)
```

### Testing Webhooks Locally

1. **Start the system:**
```bash
docker-compose up -d --build
```

2. **Use ngrok for tunneling:**
```bash
ngrok http 8086
```

3. **Configure webhook in GitHub** with the ngrok URL

4. **Push a model change:**
```bash
echo "# test" >> models/test_model.pkl
git add models/test_model.pkl
git commit -m "Test webhook"
git push
```

5. **Verify in logs:**
```bash
docker logs -f model_server_api
```

### Testing Model Lifecycle

```bash
# List models
curl http://localhost:8086/models

# Activate a model
curl -X POST http://localhost:8086/activate/rf_model

# Check status
curl http://localhost:8086/status/rf_model

# Make prediction
curl -X POST http://localhost:8086/predict/rf_model \
  -H "Content-Type: application/json" \
  -d '{"input": [[1.0, 2.0, 3.0]]}'

# Deactivate
curl -X POST http://localhost:8086/deactivate/rf_model
```

## Docker Deployment

The system uses Docker Compose for containerized deployment with two services:

### Services Overview

**1. flask_api (model_server_api)**
- Main API server for model management and predictions
- Exposes port 8086
- Mounts Docker socket for TensorFlow Serving container management
- Uses named volume `models_data` for persistent model storage

**2. model_syncer** (local filesystem mode only)
- Syncs models from host `./models/` to the shared Docker volume
- Only active when using `MODEL_SOURCE=local_filesystem`
- Activated via Docker Compose profiles

### Key Configuration Details

**Named Volume Strategy:**
```yaml
volumes:
  models_data:  # Shared between flask_api and model_syncer
```
This ensures model persistence and enables the syncer to update models that the API serves.

**Docker Socket Mounting:**
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```
Allows the Flask API to create and manage TensorFlow Serving containers dynamically.

**Profile-Based Activation:**
The `model_syncer` service only runs in local filesystem mode. To start with syncer:
```bash
docker-compose --profile local_filesystem up -d
```

For GitHub mode (no syncer needed):
```bash
docker-compose up -d
```

### Starting the System

**GitHub Mode:**
```bash
# Ensure .env has MODEL_SOURCE=github
docker-compose up -d --build
```

**Local Filesystem Mode:**
```bash
# Ensure .env has MODEL_SOURCE=local_filesystem
docker-compose --profile local_filesystem up -d --build
```

### Viewing Logs

```bash
# API logs
docker logs -f model_server_api

# Syncer logs (if running)
docker logs -f model_syncer

# All services
docker-compose logs -f
```

### TensorFlow Serving Integration

TensorFlow SavedModels are automatically deployed in individual TF Serving containers:

- Each SavedModel gets its own container (e.g., `tfserving-fire_savedmodel`)
- Created dynamically when model is activated
- Removed automatically when model is deactivated
- Internal communication via `model_server_net` network
- No manual port configuration needed

## Logging

The system provides comprehensive logging with clear prefixes:

```
[INIT]      - Initialization and startup
[REGISTRY]  - Model registry operations
[LIFECYCLE] - Model activation/deactivation
[SYNC]      - Synchronization events
[WEBHOOK]   - GitHub webhook events
[WATCHER]   - Filesystem monitoring
[SHUTDOWN]  - Cleanup and shutdown
```

View logs:
```bash
docker logs -f model_server_api
```

## Troubleshooting

### Common Issues

**Models not appearing:**
- Verify `MODELS_PATH` is correct in `.env`
- Check Docker volume is mounted correctly
- Ensure model files are complete and valid
- For local mode: check `model_syncer` logs

**Activation fails:**
- Check model file format is supported
- Verify sufficient memory/disk space
- Review logs: `docker logs model_server_api`

**Predictions fail:**
- Verify input format matches model expectations
- Check model is activated (`/status/<model_name>`)
- Review model info in `/help` endpoint

**Webhook not working:**
- Verify endpoint is publicly accessible (use ngrok for testing)
- Check GitHub webhook delivery logs
- Ensure `MODEL_SOURCE=github` in `.env`
- Check API logs for `[WEBHOOK]` messages

**TensorFlow Serving container issues:**
- Verify Docker socket is mounted: `/var/run/docker.sock`
- Check `model_server_net` network exists
- Review TF Serving logs: `docker logs tfserving-<model_name>`

