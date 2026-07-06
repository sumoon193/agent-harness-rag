"""
应用层自定义异常层次。

所有业务异常必须继承 AppError，API 层捕获这些异常并映射为 HTTP 状态码。
"""


class AppError(Exception):
    """应用层基础异常"""
    pass


class NotFoundError(AppError):
    """资源不存在"""
    pass


class PermissionError(AppError):
    """权限不足"""
    pass


class ValidationError(AppError):
    """业务校验失败"""
    pass


class ExternalServiceError(AppError):
    """外部服务调用失败（Milvus、ES、LLM API 等）"""
    pass
