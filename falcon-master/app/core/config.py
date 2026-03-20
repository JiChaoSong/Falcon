from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Falcon"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # FastAPI/Starlette 需要的是 list[str]，这里给出安全默认值
    CORS_ORIGINS: list[str] = Field(default_factory=list) if not DEBUG else ["*"]
    CORS_ORIGIN_WHITELIST: Any = ()

    REQUEST_LOGGING: bool = True
    ENVIRONMENT: str = "local"

    HOST: str = "127.0.0.1"
    PORT: int = 8008

    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/perflocust"

    POOL_PRE_PING: bool = True
    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 20
    POOL_RECYCLE: int = 1800
    POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False
    ID_NODE_ID: int = 1

    LOG_LEVEL: str = "INFO"

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    SECRET_KEY: str = "change-me-secret-key"
    REFRESH_SECRET_KEY: str = "change-me-refresh-secret-key"
    ALGORITHM: str = "HS256"

    AUTH_WHITELIST: list[str] = Field(
        default_factory=lambda: [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/user/login",
            "/health",
            "/docs/oauth2-redirect",
            "/favicon.ico",
        ]
    )

    GRPC_MASTER_HOST: str = "127.0.0.1"
    GRPC_MASTER_PORT: int = 50051
    WORKER_SHARED_TOKEN: str = "change-me-worker-token"
    GRPC_WORKER_TAGS: str = ""
    GRPC_WORKER_METADATA_JSON: str = "{}"
    GRPC_WORKER_CAPACITY: int = 4
    GRPC_WORKER_HEARTBEAT_TIMEOUT_SECONDS: int = 15
    GRPC_WORKER_HISTORY_RETENTION_SECONDS: int = 86400
    GRPC_SCHEDULING_STRATEGY: str = "least_loaded"
    GRPC_WORKER_HEALTH_CHECK_ENABLED:bool = True
    GRPC_WORKER_HEALTH_CHECK_INTERVAL_SECONDS:int = 30

    ERROR_MSG_MAP: Optional[Dict[str, str]] = {
        "no_such_attribute": "属性不存在",
        "json_invalid": "JSON格式无效",
        "json_type": "JSON数据类型错误",
        "needs_python_object": "需要Python对象类型",
        "recursion_loop": "检测到递归循环",
        "missing": "必填字段未提交",
        "frozen_field": "不可变字段，不允许修改",
        "frozen_instance": "不可变实例，不允许修改",
        "extra_forbidden": "不允许传入未定义的额外字段",
        "invalid_key": "字段键名不合法",
        "get_attribute_error": "获取属性失败",
        "model_type": "模型类型不匹配",
        "model_attributes_type": "模型属性类型错误",
        "dataclass_type": "数据类类型不匹配",
        "dataclass_exact_type": "数据类精确类型不匹配",
        "default_factory_not_called": "默认工厂函数未执行",
        "none_required": "字段必须为null值",
        "greater_than": "数值必须大于指定值",
        "greater_than_equal": "数值必须大于等于指定值",
        "less_than": "数值必须小于指定值",
        "less_than_equal": "数值必须小于等于指定值",
        "multiple_of": "数值必须是指定数字的倍数",
        "finite_number": "数值必须为有限数",
        "too_short": "长度不足限制",
        "too_long": "长度超出限制",
        "iterable_type": "必须为可迭代对象",
        "iteration_error": "迭代操作执行失败",
        "string_type": "必须为字符串类型",
        "string_sub_type": "字符串子类型不匹配",
        "string_unicode": "必须为Unicode编码字符串",
        "string_too_short": "字符串长度过短",
        "string_too_long": "字符串长度过长",
        "string_pattern_mismatch": "字符串格式与正则规则不匹配",
        "enum": "值不在枚举允许范围内",
        "dict_type": "必须为字典类型",
        "mapping_type": "必须为映射类型",
        "list_type": "必须为列表类型",
        "tuple_type": "必须为元组类型",
        "set_type": "必须为集合类型",
        "set_item_not_hashable": "集合元素不可哈希，无法存入",
        "frozen_set_type": "必须为不可变集合类型",
        "bool_type": "必须为布尔类型",
        "bool_parsing": "布尔值解析失败",
        "int_type": "必须为整数类型",
        "int_parsing": "整数解析失败",
        "int_parsing_size": "整数数值超出解析范围",
        "int_from_float": "无法从浮点数转换为整数",
        "float_type": "必须为浮点数类型",
        "float_parsing": "浮点数解析失败",
        "complex_type": "必须为复数类型",
        "complex_str_parsing": "复数字符串解析失败",
        "bytes_type": "必须为字节类型",
        "bytes_too_short": "字节长度过短",
        "bytes_too_long": "字节长度过长",
        "bytes_invalid_encoding": "字节编码格式不合法",
        "date_type": "必须为日期类型",
        "date_parsing": "日期解析失败",
        "date_from_datetime_parsing": "从日期时间解析日期失败",
        "date_from_datetime_inexact": "日期时间无法精确转换为日期",
        "date_past": "日期必须为过去时间",
        "date_future": "日期必须为未来时间",
        "time_type": "必须为时间类型",
        "time_parsing": "时间解析失败",
        "datetime_type": "必须为日期时间类型",
        "datetime_parsing": "日期时间解析失败",
        "datetime_object_invalid": "日期时间对象不合法",
        "datetime_from_date_parsing": "从日期解析日期时间失败",
        "datetime_past": "日期时间必须为过去时间",
        "datetime_future": "日期时间必须为未来时间",
        "timezone_naive": "必须为无时区时间",
        "timezone_aware": "必须为带时区时间",
        "timezone_offset": "时区偏移量不合法",
        "time_delta_type": "必须为时间间隔类型",
        "time_delta_parsing": "时间间隔解析失败",
        "is_instance_of": "必须是指定类的实例",
        "is_subclass_of": "必须是指定类的子类",
        "callable_type": "必须为可调用对象",
        "union_tag_invalid": "联合类型标签无效",
        "union_tag_not_found": "未找到联合类型标签",
        "arguments_type": "函数参数类型错误",
        "missing_argument": "缺少必填函数参数",
        "unexpected_keyword_argument": "传入了未定义的关键字参数",
        "missing_keyword_only_argument": "缺少关键字-only参数",
        "unexpected_positional_argument": "传入了多余的位置参数",
        "missing_positional_only_argument": "缺少位置-only参数",
        "multiple_argument_values": "参数被重复赋值",
        "url_type": "必须为URL格式",
        "url_parsing": "URL解析失败",
        "url_syntax_violation": "URL语法不合法",
        "url_too_long": "URL长度超出限制",
        "url_scheme": "URL协议头不合法",
        "uuid_type": "必须为UUID格式",
        "uuid_parsing": "UUID解析失败",
        "uuid_version": "UUID版本不匹配",
        "decimal_type": "必须为高精度小数类型",
        "decimal_parsing": "高精度小数解析失败",
        "decimal_max_digits": "高精度小数总位数超出限制",
        "decimal_max_places": "高精度小数小数位数超出限制",
        "decimal_whole_digits": "高精度小数整数位数超出限制",
        "value_error": "数值格式不合法",
        "assertion_error": "断言校验失败",
        "literal_error": "字面量值不匹配",
        "missing_sentinel_error": "未检测到标记值",
    }

settings = Settings()
