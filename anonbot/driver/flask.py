'''flask 驱动适配'''

import logging
from typing_extensions import override
from typing import Any, Tuple, Optional

from anonbot.driver import Request
from anonbot.driver import WSGIMixin
from anonbot.log import LoggingHandler
from anonbot.driver import HTTPServerSetup
from anonbot.internal.driver import FileTypes

from flask import request, Flask, Response
from werkzeug.datastructures import FileStorage
from waitress import serve

logger = logging.Logger('websocket.client', 'INFO')
logger.addHandler(LoggingHandler())

class Mixin(WSGIMixin):
    '''flask 混入驱动适配'''
    
    def __init__(self) -> None:
        super().__init__()
        
        self._server_app = Flask(__name__)
    
    @property
    @override
    def type(self) -> str:
        return 'flask'
    
    @property
    @override
    def server_app(self) -> Flask:
        '''`Flask` 对象'''
        return self._server_app
    
    @property
    @override
    def wsgi(self) -> Flask:
        '''`gunicorn.app.wsgiapp` 对象'''
        return self._server_app
    
    @override
    def setup_http_server(self, setup: HTTPServerSetup) -> None:
        def _handle() -> Response:
            return self._handle_http(setup)
        
        self._server_app.add_url_rule(
            setup.path.path,
            view_func=_handle,
            methods=[setup.method]
        )
    
    @override
    def startup(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *,
        app: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        '''使用 `waitress` 启动 Flask'''
        logger = logging.getLogger('waitress')
        logger.addHandler(LoggingHandler())
        
        serve(
            app or self.server_app,
            host=host,
            port=port,
            **kwargs
        )
    
    def _handle_http(self, setup: HTTPServerSetup) -> Response:
        json: Any = None
        try:
            json = request.get_json()
        except:
            json = None
        
        data: Optional[dict] = None
        files: Optional[list[Tuple[str, FileTypes]]] = None
        try:
            data = {}
            files = []
            for key, value in request.files.items():
                if isinstance(value, FileStorage):
                    files.append(
                        (key, (value.filename, value.stream, value.content_type))
                    )
                else:
                    data[key] = value
            for key, value in request.form.items():
                data[key] = value
        except:
            data = None
            files = None
        
        http_request = Request(
            request.method,
            str(request.url),
            headers=list(request.headers.items()),
            cookies=request.cookies,
            content=request.data,
            data=data,
            json=json,
            files=files,
            version=request.environ.get('SERVER_PROTOCOL', 'HTTP/1.1'),
        )
        
        response = setup.handle_func(http_request)
        return Response(
            response.content, response.status_code, dict(response.headers.items())
        )
