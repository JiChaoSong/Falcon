from app.enums.base import AbstractBaseCodeMessageEnum


class ResponseEnums:

    SUCCESS = AbstractBaseCodeMessageEnum(code = 20000, message = '请求成功')

    TOKEN_INVALID = AbstractBaseCodeMessageEnum(code = 40001, message = '登录信息失效，请重新登录！')
    FORBIDDEN = AbstractBaseCodeMessageEnum(code = 40003, message = '权限不足, 请联系系统管理员')
    PAGE_NOT_FOUND = AbstractBaseCodeMessageEnum(code = 40004, message = 'Page Not Found')
    METHOD_NOT_ALLOW = AbstractBaseCodeMessageEnum(code = 40005, message = 'Method Not Allow')

    USER_NAME_IS_NOT_EXIST = AbstractBaseCodeMessageEnum(code = 41000, message = '用户名不存在')
    USER_PASSWORD_IS_ERROR = AbstractBaseCodeMessageEnum(code = 41001, message = '密码错误')
    USER_STATUS_IS_FALSE = AbstractBaseCodeMessageEnum(code = 41002, message = '用户状态不合法')
    USER_IS_NOT_EXIST_BY_ID = AbstractBaseCodeMessageEnum(code = 41003, message = '用户不存在')
    DATA_DICT_NOT_EXIST_BY_ID = AbstractBaseCodeMessageEnum(code = 41004, message = '数据字典不存在')

    SYSTEM_EXCEPTION = AbstractBaseCodeMessageEnum(code = 50000, message = '系统异常')