# Falcon Deploy

本目录提供基于以下四个目录的独立部署文件：

- `falcon-master`
- `falcon-worker`
- `falcon-shared`
- `falcon-ui`

## 文件说明

- `falcon-master.Dockerfile`
  用于构建 `falcon-master` 镜像
- `falcon-worker.Dockerfile`
  用于构建 `falcon-worker` 镜像
- `falcon-ui.Dockerfile`
  用于构建 `falcon-ui` 前端镜像
- `falcon-ui.nginx.conf`
  UI 容器的 nginx 配置，包含 SPA 路由回退以及 `/api`、`/ws` 反向代理
- `docker-compose.yml`
  本地一键拉起 `mysql + falcon-master + falcon-worker + falcon-ui`
- `.env.master.example`
  `falcon-master` 环境变量示例
- `.env.worker.example`
  `falcon-worker` 环境变量示例

## 使用方式

1. 复制环境变量文件

```powershell
Copy-Item .\deploy\.env.master.example .\deploy\.env.master
Copy-Item .\deploy\.env.worker.example .\deploy\.env.worker
```

2. 在项目根目录执行 compose

```powershell
docker compose -f .\deploy\docker-compose.yml up --build -d
```

3. 首次启动后执行数据库迁移

```powershell
docker exec -it falcon-master alembic upgrade head
```

## 端口

- `8080`：前端 UI
- `8008`：master HTTP API
- `50051`：master gRPC control plane
- `50061`：worker gRPC service
- `3306`：MySQL

## 说明

- 当前 Docker 构建完全基于 `falcon-master / falcon-worker / falcon-shared / falcon-ui` 四目录。
- `falcon-shared` 在镜像构建阶段会先作为本地包安装。
- `falcon-ui` 构建时默认使用 `VITE_API_BASE_URL=/api`，运行时由 nginx 代理到 `falcon-master:8008`。
- 如需多 worker，可在 compose 中复制 `falcon-worker` 服务并修改 `GRPC_WORKER_ID`、端口和标签。
