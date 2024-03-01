'''AnonBot 运行的配置项

配置本身使用 YAML 文件格式'''

from datetime import timedelta
from typing import TYPE_CHECKING, Any, Self, Union, Optional

import yaml

from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseConfig(BaseSettings):
    
    model_config = SettingsConfigDict(extra='allow')
    
    if TYPE_CHECKING:
        def __getattr__(self, name: str) -> Any:
            return self.__dict__.get(name)
    
    def get(self, name: str, default: Any = None) -> Any:
        return self.model_dump().get(name, default)
    
    @classmethod
    def load_from_yaml(cls, path: str) -> Self:
        with open(path, 'r') as file:
            data = yaml.safe_load(file)
        return cls.model_validate(data)

class Config(BaseConfig):
    log_level: Union[int, str] = 'INFO'
    '''日志等级'''
    api_timeout: Optional[float] = 30.0
    '''API 请求超时时间'''
    superusers: set[str] = set()
    '''超级用户列表'''
    session_expire_timeout: timedelta = timedelta(minutes=5)
    '''会话过期时间'''
