from typing import Optional
from yarl import URL
from pydantic import Field, BaseModel

class ClientInfo(BaseModel):
    host: str = 'localhost'
    '''服务端地址'''
    port: int
    '''服务端端口'''
    path: str = ''
    '''服务端路径'''
    token: Optional[str] = None
    '''服务端token'''
    
    @property
    def identity(self) -> str:
        return f'{self.host}:{self.port}'
    
    @property
    def api_base(self) -> URL:
        return URL(f'http://{self.host}:{self.port}') / self.path.lstrip('/') / 'v1'
    
    @property
    def ws_base(self) -> URL:
        return URL(f'ws://{self.host}:{self.port}') / self.path.lstrip('/') / 'v1'

class Config(BaseModel):
    clients: list[ClientInfo] = Field(default_factory=list)
    '''客户端配置列表'''
