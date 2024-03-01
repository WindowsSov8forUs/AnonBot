from enum import IntEnum
from datetime import datetime
from typing import Any, Union, Literal, Optional

from pydantic import BaseModel, Field, validator, model_validator

from anonbot.adapter import (
    Login as Login,
    GuildMember as Member,
    MessageModel as Message
)

class InnerMember(Member):
    
    @validator('joined_at', pre=True)
    def parse_joined_at(cls, v: Any) -> Optional[datetime]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError as exception:
            raise ValueError(f'Invalid timestamp: {v}') from exception
        return datetime.fromtimestamp(timestamp / 1000)

class OuterMember(InnerMember):
    user: 'User'
    joined_at: datetime

class InnerMessage(Message):
    
    @model_validator(mode='before')
    def ensure_content(cls, values: dict[str, Any]) -> dict[str, Any]:
        if 'content' in values:
            return values
        return {**values, 'content': ''}
    
    @validator('created_at', pre=True)
    def parse_created_at(cls, v: Any) -> Optional[datetime]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError as exception:
            raise ValueError(f'Invalid timestamp: {v}') from exception
        return datetime.fromtimestamp(timestamp / 1000)
    
    @validator('updated_at', pre=True)
    def parse_updated_at(cls, v: Any) -> Optional[datetime]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError as exception:
            raise ValueError(f'Invalid timestamp: {v}') from exception
        return datetime.fromtimestamp(timestamp / 1000)

class OuterMessage(InnerMessage):
    channel: 'Channel'
    guild: 'Guild'
    user: 'User'

class OuterLogin(Login):
    user: 'User'
    self_id: str
    platform: str

class Event(BaseModel):
    id: int
    type: str
    platform: str
    self_id: str
    timestamp: datetime
    argv: Optional['Argv'] = None
    button: Optional['Button'] = None
    channel: Optional['Channel'] = None
    guild: Optional['Guild'] = None
    login: Optional['Login'] = None
    member: Optional[InnerMember] = None
    message: Optional[InnerMessage] = None
    operator: Optional['User'] = None
    role: Optional['Role'] = None
    user: Optional['User'] = None
    _type: Optional[str] = None
    _data: Optional[dict[str, Any]] = None
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            return v
        try:
            timestamp = int(v)
        except ValueError as exception:
            raise ValueError(f'Invalid timestamp: {v}') from exception
        return datetime.fromtimestamp(timestamp / 1000)

class Opcode(IntEnum):
    EVENT = 0
    PING = 1
    PONG = 2
    IDENTIFY = 3
    READY = 4

class Payload(BaseModel):
    op: Opcode = Field(...)
    body: Optional[dict[str, Any]] = Field(None)

class Identify(BaseModel):
    token: Optional[str] = None
    sequence: Optional[int] = None

class Ready(BaseModel):
    logins: list[OuterLogin]

class IdentifyPayload(Payload):
    op: Literal[Opcode.IDENTIFY] = Field(Opcode.IDENTIFY)
    body: Identify

class ReadyPayload(Payload):
    op: Literal[Opcode.READY] = Field(Opcode.READY)
    body: Ready

class PingPayload(Payload):
    op: Literal[Opcode.PING] = Field(Opcode.PING)

class PongPayload(Payload):
    op: Literal[Opcode.PONG] = Field(Opcode.PONG)

class EventPayload(Payload):
    op: Literal[Opcode.EVENT] = Field(Opcode.EVENT)
    body: Event

PayloadType = Union[
    Union[IdentifyPayload, ReadyPayload, PingPayload, PongPayload, EventPayload],
    Payload
]

from anonbot.adapter import (
    Argv as Argv,
    User as User,
    Guild as Guild,
    Button as Button,
    GuildRole as Role,
    Channel as Channel,
    EventType as EventType,
    Pagination as Pagination,
    ChannelType as ChannelType,
    LoginStatus as LoginStatus
)
