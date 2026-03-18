# Falcon

Falcon 是一个基于 `FastAPI + Vue 3` 的压测平台项目，当前已经完成了管理平台主链路，并落地了 M1 版本的自研执行器骨架。

当前项目的定位不是“只有页面的后台原型”，而是已经具备以下两层能力：

1. 压测管理平台
2. 单机可运行的任务执行与监控能力

项目当前更适合被理解为：

“管理域已成型，执行域进入 M1 可运行阶段的压测平台。”

## 当前功能

### 1. 用户与权限

- 登录、鉴权、登录失效自动跳转登录页
- 用户管理放在“设置”中
- 支持用户新增、编辑、删除、启停、重置密码
- 超级管理员与普通用户区分
- 超级管理员不能禁用自己
- 项目级数据权限隔离已生效

### 2. 项目管理

- 项目列表、筛选、新增、编辑、删除
- 项目详情展示
- 项目负责人选择真实用户
- 项目成员管理
- 项目成员与项目级数据权限联动

### 3. 用例管理

- 用例列表、筛选、新增、编辑、删除
- 用例复制、预览、批量启用/停用/删除
- 用例按项目归属
- 用例导入 Phase 1
  - 支持 OpenAPI URL
  - 支持 OpenAPI JSON 导入
  - 支持导入预览
  - 支持重复检测和跳过/覆盖策略

### 4. 场景管理

- 场景列表、筛选、新增、编辑、删除、复制、预览
- 场景绑定项目
- 场景绑定项目下的用例
- 用例顺序按列表顺序自动维护
- 权重支持编辑，并校验合计为 `100`

### 5. 任务管理

- 任务列表、筛选、新增、编辑、删除、预览
- 任务绑定项目、负责人、场景
- 任务负责人默认当前登录用户
- 任务场景编排支持排序
- 仅在选择项目后加载该项目下场景
- 支持执行策略
  - `sequential`
  - `weighted`
- 支持任务场景配置
  - `order`
  - `weight`
  - `target_users`

### 6. 监控与报告

- 任务监控页接入真实运行数据
- 支持任务启动、停止
- 展示实时状态、RPS、响应时间、失败率、趋势图
- 展示场景/接口级统计明细
- 支持最近运行历史切换
- 支持基础运行报告
- 支持独立任务报告页

### 7. 执行器 M1

当前已落地 M1 版本单机执行器：

- `/task/run`
- `/task/stop`
- `/task/status`
- `/task/runs`
- `/task/report`

执行器能力包括：

- 单机任务运行
- 按 `task -> scenario -> case` 执行
- HTTP 请求执行
- 秒级指标聚合
- 任务运行实例记录
- 历史运行报告查询
- 并发用户与爬升速率基础支持
- `sequential / weighted` 两种任务场景执行策略

## 当前边界

当前项目已经可以完成管理闭环和单机运行闭环，但仍然处于平台建设阶段。

暂未完成的核心能力包括：

- 分布式 worker 调度
- worker 注册与心跳
- gRPC / WebSocket worker control
- 多协议执行器
- 完整报告中心
- 长期历史趋势分析
- 更细粒度角色权限
- 生产级高性能压测引擎优化

## 技术栈

### 后端

- FastAPI
- SQLAlchemy 2.x
- Alembic
- MySQL
- PyMySQL
- JWT

### 前端

- Vue 3
- TypeScript
- Vite
- Pinia
- Ant Design Vue
- ECharts

## 项目结构

```text
prelocust/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/            # 接口层
│   │   ├── engine_v2/      # M1 自研执行器
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── services/       # 业务服务
│   │   └── utils/
│   ├── alembic/            # 数据库迁移
│   ├── requirements.txt
│   └── main.py
├── frontend/               # Vue 前端
│   ├── src/
│   │   ├── api/
│   │   ├── layout/
│   │   ├── router/
│   │   ├── store/
│   │   ├── types/
│   │   └── views/
│   └── package.json
├── docs/
│   └── distributed-engine-design.md
└── README.md
```

## 架构图

当前项目采用前后端分离架构，管理平面与单机执行器共用同一个 FastAPI 服务，监控数据通过任务运行状态接口聚合并返回前端。

```mermaid
flowchart LR
    UI["Frontend (Vue 3)"] --> API["FastAPI API Layer"]
    API --> SVC["Service Layer"]
    SVC --> DB["MySQL"]
    SVC --> ENG["engine_v2 (M1 单机执行器)"]
    ENG --> TARGET["Target Services"]
    ENG --> DB

    subgraph Frontend
        UI
    end

    subgraph Backend
        API
        SVC
        ENG
    end
```

## 模块职责

### 1. 前端 `frontend/src`

- `api/`：封装项目、用例、场景、任务、用户等接口请求
- `views/`：页面级实现，包括任务管理、监控页、报告页、登录页等
- `layout/`：整体布局与监控页组件编排
- `store/`：用户登录态与前端全局状态管理
- `utils/`：请求封装、鉴权、菜单、工具函数等

### 2. 后端接口层 `backend/app/api`

- 对外暴露 REST 接口
- 接收前端请求并完成参数校验
- 将业务处理委托给 `services/`
- 当前核心接口集中在用户、项目、用例、场景、任务与运行控制

### 3. 业务服务层 `backend/app/services`

- 实现项目、用例、场景、任务等核心业务逻辑
- 处理数据权限校验、关联关系维护、任务运行编排
- `task_runtime_service.py` 负责启动、停止、查询任务运行状态和报告

### 4. 数据模型层 `backend/app/models`

- 定义 `Project`、`Case`、`Scenario`、`Task`、`TaskRun`、`TaskMetricSecond` 等核心表结构
- 承载管理数据、运行历史和秒级监控指标

### 5. 模式定义层 `backend/app/schemas`

- 定义请求体与响应体结构
- 为 FastAPI 提供统一的数据校验和响应模型

### 6. 中间件与基础设施 `backend/app/core`、`backend/app/middleware`

- `core/config.py`：环境变量与全局配置
- `core/security.py`：认证鉴权相关能力
- `middleware/auth.py`：登录鉴权
- `middleware/request_context.py`：请求上下文与日志辅助
- `handler/validation_exception.py`：统一处理参数校验错误

### 7. 自研执行器 `backend/app/engine_v2`

- `runtime/`：任务、场景、用例三级运行时执行逻辑
- `protocol/`：协议执行器，M1 以 HTTP 为主
- `metrics/`：本地指标聚合，按秒汇总 RPS、响应时间、失败数等
- `registry/`：运行中的任务注册与控制对象管理

### 8. 数据库迁移 `backend/alembic`

- 管理表结构演进
- 当前已包含任务运行表、秒级指标表、执行策略等相关迁移

## 数据流

当前任务运行主链路如下：

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as FastAPI
    participant SVC as TaskRuntimeService
    participant ENG as TaskRunner
    participant DB as MySQL
    participant TG as Target Service

    FE->>API: POST /task/run
    API->>SVC: run(task_id)
    SVC->>DB: 创建 TaskRun 记录
    SVC->>ENG: 创建异步运行任务
    ENG->>DB: 更新任务状态为 running
    loop 任务执行期间
        ENG->>TG: 执行 scenario/case HTTP 请求
        ENG->>ENG: 聚合秒级指标
        ENG->>DB: 写入 task_metrics_second
    end
    FE->>API: POST /task/status /task/runs /task/report
    API->>SVC: 查询运行状态/历史/报告
    SVC->>DB: 读取 TaskRun 与指标快照
    API-->>FE: 返回监控与报告数据
```

补充说明：

- 当前监控页主要基于轮询 `/task/status`、`/task/runs`、`/task/report` 拉取数据
- `engine_v2` 当前是 M1 单机模式，执行器与控制平面尚未拆分为独立 worker
- `docs/distributed-engine-design.md` 描述的是后续 M2/M3 阶段的分布式演进方向

## 环境要求

- Python 3.11+
- Node.js 18+
- pnpm 8+
- MySQL 8+

## 后端启动

### 1. 安装依赖

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制并修改环境变量文件：

```bash
cp .env.example .env
```

示例配置如下：

```env
PROJECT_NAME='Falcon'
VERSION='1.0.0'
HOST='127.0.0.1'
DEBUG=True
PORT=8008
DATABASE_URL='mysql+pymysql://user:password@localhost:3306/perflocust'
SECRET_KEY='your-secret-key'
REFRESH_SECRET_KEY='your-refresh-secret-key'
ALGORITHM=HS256
```

### 3. 执行数据库迁移

```bash
cd backend
alembic upgrade head
```

### 4. 启动后端

```bash
cd backend
python main.py
```

默认地址：

- API: [http://127.0.0.1:8008](http://127.0.0.1:8008)
- Swagger: [http://127.0.0.1:8008/docs](http://127.0.0.1:8008/docs)

## 前端启动

### 1. 安装依赖

```bash
cd frontend
pnpm install
```

### 2. 启动开发环境

```bash
pnpm dev
```

### 3. 打包构建

```bash
pnpm build
```

## 核心数据模型

当前项目的核心业务链路如下：

1. 项目 `Project`
2. 用例 `Case`
3. 场景 `Scenario`
4. 任务 `Task`
5. 任务运行实例 `TaskRun`

关系说明：

- 一个项目下可以有多个用例
- 一个场景可以绑定多个用例
- 一个任务可以编排多个场景
- 一个任务可以产生多次运行实例
- 每次运行实例会产生监控指标和报告摘要

## 已实现的关键设计

### 1. 非自增 ID

当前项目已经不再依赖 MySQL 自增 ID，而是由应用层统一生成安全整数 ID。

### 2. 项目级数据权限

普通用户只能看到自己参与项目下的数据，管理员可查看全量数据。

### 3. 单机执行器 M1

M1 版本先以内嵌执行器方式运行，不引入真正的分布式 worker。

### 4. 运行历史与报告

一个任务可以有多次运行实例，并按实例查询报告。

## 常用接口

### 用户

- `/user/login`
- `/user/info`
- `/user/list`
- `/user/create`
- `/user/update`
- `/user/delete`

### 项目

- `/project/list`
- `/project/create`
- `/project/update`
- `/project/delete`
- `/project/member/list`

### 用例

- `/case/list`
- `/case/create`
- `/case/update`
- `/case/delete`
- `/case/import/preview`
- `/case/import/commit`

### 场景

- `/scenario/list`
- `/scenario/create`
- `/scenario/update`
- `/scenario/delete`

### 任务与执行

- `/task/list`
- `/task/create`
- `/task/update`
- `/task/delete`
- `/task/run`
- `/task/stop`
- `/task/status`
- `/task/runs`
- `/task/report`

## 开发建议

当前最适合继续推进的方向：

1. 任务执行器能力继续增强
2. 运行报告中心完善
3. 分布式 worker 设计进入 M2
4. 实时监控与结果沉淀继续细化

建议优先级：

1. 执行器并发模型与执行语义继续增强
2. 报告对比与运行历史体验完善
3. worker 注册与调度方案落地
4. 分布式执行链路演进

## 设计文档

执行引擎设计文档见：

- [docs/distributed-engine-design.md](/Users/songjihcao/PycharmProjects/prelocust/docs/distributed-engine-design.md)

## 当前状态总结

当前项目已经完成了：

- 管理平台主链路
- 真实前后端联调
- 基础权限体系
- M1 单机执行器
- 实时监控
- 基础运行报告

下一阶段的重点，不再是单纯补管理页面，而是继续把执行器、运行报告和分布式能力做深。
---

## 最近更新

下面这部分用于补充当前代码已经落地、但旧 README 尚未完整覆盖的内容。

### 1. 控制面 + gRPC worker_runtime 已落地

当前执行架构已经不是单进程内嵌执行器，而是：

- 控制面：`backend/main.py`
- 独立 worker 入口：`backend/worker_app.py`
- worker 运行时代码：`backend/app/worker_runtime`

任务运行流程已经变成：

1. 前端调用 `/task/run`
2. 控制面创建 `task_run`
3. 控制面通过 gRPC 把任务分发给 worker_runtime
4. worker_runtime 本地执行 `engine_v2`
5. worker_runtime 通过 gRPC 回传 `started / snapshot / finished / failed / canceled`
6. 控制面落库并通过 WebSocket 推送给前端监控页

### 2. worker 注册、心跳、节点管理已补齐

当前 worker 相关能力包括：

- gRPC 注册
- gRPC 心跳
- 节点标签
- 节点容量
- 节点调度权重
- 心跳超时离线
- 历史节点自动清理

当前保留的节点管理 HTTP 接口主要用于查询和人工操作：

- `/worker/list`
- `/worker/info`
- `/worker/update`

说明：

- worker 自动注册和心跳已经不再走 HTTP
- 节点管理页可以查看和更新节点状态、容量、权重、标签等信息

### 3. worker 配置已独立

现在配置分成两套：

- 控制面：`backend/.env`
- worker_runtime：`backend/.env.worker`

对应模板文件：

- `backend/.env.example`
- `backend/.env.worker.example`

worker 还支持通过指定配置文件启动：

```bash
cd backend
.venv\Scripts\python.exe worker.py --env-file E:\pycharmProject\Falcon\backend\.env.worker
```

### 4. WebSocket 监控链已接通

任务监控页当前优先使用 WebSocket：

- 任务运行开始后，控制面会把运行事件推送到监控页
- 监控页不再依赖高频全量轮询
- WebSocket 断开时由前端做降级处理

当前监控和报告页已支持展示：

- RPS 趋势
- 平均响应时间 / P95 / P99
- 失败趋势
- 状态码分布
- 错误类型分布
- 失败样本
- 运行摘要与报告下载

### 5. 执行引擎能力已增强

`backend/app/engine_v2` 目前已经补上的能力包括：

- `httpx.AsyncClient` 异步 HTTP 执行
- 响应断言
- 响应提取
- 运行时变量渲染
- 秒级指标聚合
- 失败分类与样本保留

已经补到执行链中的运行时能力包括：

- `expected_status`
- `expected_response_time`
- `contains`
- `not_contains`
- `equals`
- `json path` 提取

### 6. 时间策略已统一

当前系统时间策略如下：

- 数据库存储统一使用 UTC
- 后端内部计算统一使用 UTC
- 接口展示时间统一转换为北京时间
- 前端统一按 `Asia/Shanghai` 渲染

这样可以同时保证：

- 分布式节点间计算一致
- 心跳超时和运行时长计算稳定
- 页面展示仍符合本地使用习惯

### 7. 前端页面已新增和调整

最近补充和调整的前端页面包括：

- 任务监控页：接入 WebSocket 和更完整的图表
- 任务报告页：增加趋势图、分布图和下载能力
- 系统设置页：增加节点管理
- 用户相关：新增个人中心、账户设置

### 8. 当前建议的启动顺序

本机联调建议按下面顺序启动：

1. MySQL
2. 控制面 `backend/main.py`
3. worker_runtime `backend/worker_app.py`
4. 前端 `frontend`

常用地址：

- 控制面 HTTP：`http://127.0.0.1:8008`
- 控制面 gRPC：`127.0.0.1:50051`
- worker gRPC：`127.0.0.1:50061`
- 前端开发环境：`http://127.0.0.1:5173`

### 9. 当前版本定位

如果用一句话概括当前状态：

这是一个“管理面基本成型、单控制面 + gRPC worker 已打通、实时监控和报告可用、正在向更完整分布式压测平台演进”的版本。
