import json
from typing_extensions import override
from typing import Any, Literal, Optional

from pydantic import TypeAdapter

from anonbot import threading
from anonbot.log import logger
from anonbot.exception import WebSocketClosed
from anonbot.adapter import Adapter as BaseAdapter
from anonbot.driver import Driver, Request, WebSocket, HTTPClientMixin, WebSocketClientMixin

from .bot import Bot
from .config import Config, ClientInfo
from .models import Event as SatoriEvent
from .event import (
    EVENT_CLASSES,
    Event,
    LoginAddedEvent,
    LoginRemovedEvent,
    LoginUpdatedEvent,
    InteractionCommandEvent
)
from .models import (
    Opcode,
    Payload,
    Identify,
    LoginStatus,
    PayloadType,
    PingPayload,
    PongPayload,
    EventPayload,
    ReadyPayload,
    IdentifyPayload
)

class Adapter(BaseAdapter):
    bots: dict[str, Bot]
    
    @override
    def __init__(self, driver: Driver, **kwargs: Any) -> None:
        super().__init__(driver, **kwargs)
        self.satori_config = Config.model_validate(self._config)
        self.tasks: list[threading.Task] = []
        self.sequences: dict[str, int] = {}
        self.setup()
    
    @classmethod
    @override
    def get_name(cls) -> str:
        return 'Satori'
    
    def setup(self) -> None:
        if not isinstance(self.driver, HTTPClientMixin):
            raise RuntimeError(f'Http client driver is not available!')
        if not isinstance(self.driver, WebSocketClientMixin):
            raise RuntimeError(f'WebSocket client driver is not available!')
        self.driver.on_startup(self.startup)
        self.driver.on_shutdown(self.shutdown)
    
    def startup(self) -> None:
        for client in self.satori_config.clients:
            task = threading.Task(self.ws, client)
            self.tasks.append(threading.create_task(task))
    
    def shutdown(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        threading.gather(
            *(threading.Task(threading.wait_for, task, timeout=10) for task in self.tasks),
            return_exceptions=True
        )
    
    @staticmethod
    def payload_to_json(payload: Payload) -> str:
        return payload.model_dump_json(by_alias=True)
    
    def receive_payload(self, info: ClientInfo, ws: WebSocket) -> Payload:
        payload: PayloadType = TypeAdapter(PayloadType).validate_python(json.loads(ws.receive())) # type: ignore
        if isinstance(payload, EventPayload):
            self.sequences[info.identity] = payload.body.id
        return payload
    
    def _authenticate(self, info: ClientInfo, ws: WebSocket) -> Optional[Literal[True]]:
        '''鉴权连接'''
        payload = IdentifyPayload(
            op=Opcode.IDENTIFY,
            body=Identify(
                token=info.token
            )
        )
        if info.identity in self.sequences:
            payload.body.sequence = self.sequences[info.identity]
        
        try:
            ws.send(self.payload_to_json(payload))
        except Exception as exception:
            logger.error(f'Error while sending Identify payload', exception=exception)
            return
        
        response = self.receive_payload(info, ws)
        if not isinstance(response, ReadyPayload):
            logger.error(f'Received unexpected payload: ', response)
            return
        for login in response.body.logins:
            if not login.self_id:
                continue
            if login.status != LoginStatus.ONLINE:
                continue
            if f'{login.platform}:{login.self_id}' not in self.bots:
                bot = Bot(self, login.self_id, login.platform, info)
                self.bot_connect(bot, login.platform)
                logger.info(f'Bot {bot.self_id} connected to {bot.platform}')
            else:
                bot = self.bots[f'{login.platform}:{login.self_id}']
            bot.on_ready(login.user)
        if not self.bots:
            logger.warn('No bots connected')
            return
        return True
    
    @threading.loop
    def _heartbeat(self, info: ClientInfo, ws: WebSocket) -> None:
        '''心跳'''
        logger.trace(f'Heartbeat at {self.sequences.get(info.identity, None)}')
        payload = PingPayload(op=Opcode.PING, body={})
        try:
            ws.send(self.payload_to_json(payload))
        except Exception as exception:
            logger.warn(f'Error while sending Ping payload: ', exception)
        threading.sleep(9)
    
    def ws(self, info: ClientInfo) -> None:
        ws_url = info.ws_base / 'events'
        request = Request('GET', ws_url, timeout=60.0)
        heartbeat_task: Optional[threading.Task] = None
        while True:
            try:
                with self.websocket(request) as ws:
                    logger.debug(f'WebSocket connected to {ws_url}')
                    try:
                        if not self._authenticate(info, ws):
                            threading.sleep(3)
                            continue
                        heartbeat_task = threading.create_task(self._heartbeat, info, ws)
                        self._loop(info, ws)
                    except WebSocketClosed as exception:
                        logger.error('WebSocket closed', exception=exception)
                    except Exception as exception:
                        logger.error(f'Error while process data from WebSocket {ws_url}', exception=exception)
                    finally:
                        if heartbeat_task:
                            heartbeat_task.cancel()
                            heartbeat_task = None
                        bots = list(self.bots.values())
                        for bot in bots:
                            self.bot_disconnect(bot, bot.platform)
                        bots.clear()
            except Exception as exception:
                logger.error(f'Error while connecting to WebSocket {ws_url}', exception=exception)
                threading.sleep(3)
    
    @threading.loop
    def _loop(self, info: ClientInfo, ws: WebSocket) -> None:
        payload = self.receive_payload(info, ws)
        logger.trace(f'Received payload: {repr(payload)}')
        if isinstance(payload, EventPayload):
            try:
                event = self.payload_to_event(payload.body)
            except Exception as exception:
                logger.warn(f'Failed to parse event payload: {payload}', exception=exception)
            else:
                if isinstance(event, LoginAddedEvent):
                    bot = Bot(self, event.self_id, event.platform, info)
                    if event.user:
                        bot.on_ready(event.user)
                    self.bot_connect(bot, event.platform)
                    logger.info(f'Bot {bot.self_id} connected to {bot.platform}')
                elif isinstance(event, LoginRemovedEvent):
                    self.bot_disconnect(self.bots[f'{event.platform}:{event.self_id}'], event.platform)
                    logger.info(f'Bot {event.self_id} disconnected from {event.platform}')
                    return
                elif isinstance(event, LoginUpdatedEvent):
                    self.bots[f'{event.platform}:{event.self_id}'].on_ready(event.user) if event.user else None
                if not (bot := self.bots.get(f'{event.platform}:{event.self_id}')):
                    logger.warn(f'Bot {event.self_id} at {event.platform} not found')
                    return
                if isinstance(event, InteractionCommandEvent):
                    event = event.convert()
                threading.create_task(bot.handle_event, event)
        elif isinstance(payload, PongPayload):
            logger.trace('Pong')
            return
        else:
            logger.warn(f'Unknown payload: {repr(payload)}')
    
    @staticmethod
    def payload_to_event(payload: SatoriEvent) -> Event:
        EventClass = EVENT_CLASSES.get(payload.type, None)
        if EventClass is None:
            logger.warn(f'Unknown event type: {payload.type}')
            event = Event.model_validate(payload)
            event.__type__ = payload.type # type: ignore
            return event
        return EventClass.model_validate(payload.model_dump())

    @override
    def _call_api(self, bot: Bot, api: str, **data: Any) -> Any:
        logger.debug(f'Bot {bot.self_id} calling API {api}')
        api_handler = getattr(bot, api, None)
        if api_handler is None:
            raise NotImplementedError(f'API {api} not implemented')
        return api_handler(**data)
