'''httpx 驱动适配'''

from typing_extensions import override

from anonbot.driver import (
    Request,
    Response,
    HTTPVersion,
    HTTPClientMixin
)

import httpx

class Mixin(HTTPClientMixin):
    '''httpx 混入驱动适配'''
    
    @property
    @override
    def type(self) -> str:
        return 'httpx'
    
    @override
    def request(self, setup: Request) -> Response:
        with httpx.Client(
            cookies=setup.cookies.jar,
            http2=setup.version == HTTPVersion.H2,
            proxies=setup.proxy,
            follow_redirects=True
        ) as client:
            response = client.request(
                setup.method,
                str(setup.url),
                content=setup.content,
                data=setup.data,
                json=setup.json,
                files=setup.files,
                headers=tuple(setup.headers.items()),
                timeout=setup.timeout
            )
            try:
                content = response.text
                if content is None or content.strip() == "" :
                    content = response.content
            except Exception:
                content = response.content
            
            return Response(
                response.status_code,
                headers=response.headers.multi_items(),
                content=content,
                request=setup
            )
