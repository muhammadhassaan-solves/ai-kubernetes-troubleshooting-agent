# AI Kubernetes Troubleshooting Agent

An AI-powered Kubernetes troubleshooting dashboard that investigates a selected
cluster, collects debugging evidence with kubectl, and generates a root cause
diagnosis with suggested fixes.


## What This Project Does

The application helps users/developers troubleshoot Kubernetes issues from a simple web dashboard.

Users can:

- Sign up and log in
- Select a Kubernetes context from local kubeconfig
- Trigger a cluster investigation
- Collect pod, log, event, deployment, and networking evidence
- Receive an AI-generated root cause analysis
- View suggested kubectl commands
- Save and view recent investigation history

## Tech Stack

- Next.js
- TypeScript
- FastAPI
- Python
- Docker
- Kubernetes
- OpenRouter
- InsForge

## Architecture

```text
Frontend Dashboard
    ↓
FastAPI Backend
    ↓
Kubernetes Investigation Layer
    ↓
AI Reasoning Layer
    ↓
Root Cause + Suggested Fix
    ↓
Frontend Diagnosis
```

## Backend API

```http
GET  /health
GET  /clusters
POST /investigate
```

### `GET /health`

Checks whether the backend service is running.

### `GET /clusters`

Reads kubeconfig contexts using kubectl and returns available Kubernetes
clusters.

### `POST /investigate`

Runs the full troubleshooting workflow:

```text
Check Pods
Read Logs
Analyze Events
Inspect Deployments
Check Networking
Run AI Reasoning
Return Diagnosis
```

## Kubernetes Checks

The investigation layer detects common Kubernetes problems such as:

- CrashLoopBackOff
- ImagePullBackOff
- ErrImagePull
- Pending pods
- Failed pods
- OOMKilled containers
- Failed scheduling
- Failed mounts
- Missing endpoints
- Service selector mismatch
- Deployment rollout issues

## Example Diagnosis

```text
Root Cause:
Application pod exited with a non-zero status.

Explanation:
The container started successfully but terminated with exit code 1.

Suggested Fix:
Inspect the startup command, environment variables, and application config.

kubectl Commands:
kubectl logs faulty-pod -n default
kubectl describe pod faulty-pod -n default

Confidence:
88%
```

## Run Locally With Docker

Create a `.env` file:

```bash
cp .env.example .env
```

Set the required values:

```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_INSFORGE_URL=
NEXT_PUBLIC_INSFORGE_ANON_KEY=
KUBECONFIG_DIR=/home/your-user/.kube
```

Start the application:

```bash
docker compose up --build
```

Open:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000/health
```

## WSL and kind cluster Note

When running Docker Compose inside WSL with a kind cluster, the backend uses host
networking so it can reach the Kubernetes API server from the kubeconfig.

## Test Failure Scenarios

The repository includes Kubernetes test manifests for common failures:

```bash
kubectl apply -f k8s-test-scenarios/
```

Scenarios include:

- CrashLoopBackOff
- ImagePullBackOff
- OOMKilled
- Service selector mismatch

## Learning Outcome

This project demonstrates how a DevOps troubleshooting workflow can be converted
into a real AI-assisted product using Kubernetes, FastAPI, Next.js, Docker, and
LLM reasoning.

## Acknowledgment

Special thanks to **Abhishek Veeramalla** for teaching and guiding in this project project.
