# gRPC worker_runtime Runbook

## Components

- Control plane: FastAPI app on `HOST:PORT`
- Control plane gRPC callback server: `GRPC_CONTROL_HOST:GRPC_CONTROL_PORT`
- worker_runtime gRPC server: `GRPC_WORKER_HOST:GRPC_WORKER_PORT`

## Default Ports

- HTTP API: `127.0.0.1:8008`
- Control plane gRPC: `127.0.0.1:50051`
- Worker gRPC: `127.0.0.1:50061`

## Start Control Plane

```powershell
cd E:\pycharmProject\Falcon\backend
..\.venv\Scripts\python.exe main.py
```

If you use `uvicorn`, keep the same application entry:

```powershell
cd E:\pycharmProject\Falcon\backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8008 --reload
```

## Start worker_runtime

```powershell
cd E:\pycharmProject\Falcon\backend
Copy-Item .env.worker.example .env.worker
..\.venv\Scripts\python.exe worker_app.py
```

## Environment Variables

Control plane settings stay in `backend/.env`.

worker_runtime settings should go into `backend/.env.worker`:

```env
GRPC_WORKER_ID=worker-local
GRPC_WORKER_HOST=127.0.0.1
GRPC_WORKER_PORT=50061
CONTROL_PLANE_BASE_URL=http://127.0.0.1:8008
GRPC_CONTROL_HOST=127.0.0.1
GRPC_CONTROL_PORT=50051
WORKER_SHARED_TOKEN=change-me-worker-token
GRPC_WORKER_TAGS=default,local
GRPC_WORKER_METADATA_JSON={"zone":"local"}
GRPC_WORKER_CAPACITY=4
GRPC_WORKER_HEARTBEAT_INTERVAL_SECONDS=5
```

## Worker Registry APIs

- `POST /worker/list`: management query for node list
- `POST /worker/info`: management query for one node
- `POST /worker/update`: update tags, capacity, weight, or disable a node

worker_runtime now registers itself and sends heartbeats through `ControlPlaneRuntime/RegisterWorker`
and `ControlPlaneRuntime/HeartbeatWorker` over gRPC. The HTTP `/worker/*` routes are kept for
management queries and manual operations.

## Runtime Flow

1. `/task/run` creates a `task_run` row and dispatches the task to a worker_runtime through gRPC.
2. The worker_runtime registers itself and sends heartbeat updates to the control plane through gRPC.
3. The worker_runtime executes the task locally and reports `started`, `snapshot`, `finished`, `failed`, or `canceled` events back to the control plane through gRPC.
4. The control plane persists runtime state and pushes websocket updates to the frontend monitor page.
5. `/task/stop` sends a gRPC stop command to the same worker_runtime using the stored `worker_task_id`.
