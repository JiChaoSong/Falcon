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
