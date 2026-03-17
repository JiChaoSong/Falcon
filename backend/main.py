from app.core.audit import register_audit_listeners
from app.core.logging_config import setup_logging
from app.handler.validation_exception import register_validation_exception_handler
from app.middleware.audit import AuditMiddleware
from app.middleware.auth import AuthMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.response_wrapper import ResponseWrapperMiddleware
from app.models.base import Base
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware

from app.api import project, case, scenario, task, user
from app.core.config import settings

# 初始化日志
setup_logging(
    log_level="INFO",
    use_json=False,  # 开发环境用控制台，生产环境用JSON
    console_color=True
)


# sql监听事件

@asynccontextmanager
async def lifespan(app: FastAPI):
    register_audit_listeners(Base)

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    description="Falcon分布式压测引擎",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    swagger_ui_css_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui.css",
    swagger_ui_js_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui-bundle.js",
)


# 数据校验错误事件
register_validation_exception_handler(app)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(AuthMiddleware)

if settings.REQUEST_LOGGING:
    app.add_middleware(RequestContextMiddleware)


# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }

@app.get("/")
async def root():
    return {
        "message": "Distributed Load Test Engine",
        "docs": "/docs" if settings.DEBUG else None,
        "version": settings.VERSION,
    }

app.include_router(project.router)
app.include_router(case.router)
app.include_router(scenario.router)
app.include_router(task.router)
app.include_router(user.router)


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",  # 修正为绝对模块路径
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="debug",  # 开启debug日志，便于定位阻塞
        access_log=True,
        loop="asyncio",  # 强制使用asyncio事件循环（关键）
        env_file=".env",
        workers=1,
    )