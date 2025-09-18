class AuthException(Exception):
    """
    自定义令牌异常AuthException
    """

    def __init__(self, message: str = None):
        self.message = message


class ServiceException(Exception):
    """
    自定义服务异常ServiceException
    """

    def __init__(self, message: str = None):
        self.message = message


class ModelValidatorException(Exception):
    """
    自定义模型校验异常ModelValidatorException
    """

    def __init__(self, message: str = None):
        self.message = message
