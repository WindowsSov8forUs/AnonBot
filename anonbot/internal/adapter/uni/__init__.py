'''用于跨平台互通的消息类型
所有适配器都需要基于此进行实现
'''
from .segment import At as At
from .segment import Br as Br
from .segment import File as File
from .segment import Link as Link
from .segment import Text as Text
from .segment import Audio as Audio
from .segment import Image as Image
from .segment import Other as Other
from .segment import Quote as Quote
from .segment import Sharp as Sharp
from .segment import Style as Style
from .segment import Video as Video
from .segment import Author as Author
from .segment import Button as Button
from .message import Message as Message
from .segment import SrcBase64 as SrcBase64
from .segment import RenderMessage as RenderMessage
from .segment import MessageSegment as MessageSegment
