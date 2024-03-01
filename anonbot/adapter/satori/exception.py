from typing import Optional

from anonbot.driver import Response
from anonbot.exception import AdapterException

class SatoriAdapterException(AdapterException):
    def __init__(self) -> None:
        super().__init__('satori')

class ActionFailed(SatoriAdapterException):
    def __init__(self, response: Response) -> None:
        self.status_code: int = response.status_code
        self.headers = response.headers
        self.content = response.content
    
    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}: {self.status_code}, headers={self.headers}, content={self.content}>'
        )
    
    def __str__(self) -> str:
        return self.__repr__()

class BadRequestException(ActionFailed):
    pass

class UnauthorizedException(ActionFailed):
    pass

class ForbiddenException(ActionFailed):
    pass

class NotFoundException(ActionFailed):
    pass

class MethodNotAllowedException(ActionFailed):
    pass

class ServerErrorException(ActionFailed):
    pass

class NetworkError(SatoriAdapterException):
    def __init__(self, msg: Optional[str] = None) -> None:
        super().__init__()
        self.msg: Optional[str] = msg
        '''错误原因'''
    
    def __repr__(self) -> str:
        return f'<NetworkError message={self.msg}>'
    
    def __str__(self) -> str:
        return self.__repr__()
