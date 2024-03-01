'''事件处理器模块'''

from anonbot.internal.processor import Processor as Processor
from anonbot.internal.processor import processors as processors
from anonbot.internal.processor import current_bot as current_bot
from anonbot.internal.processor import current_event as current_event
from anonbot.internal.processor import current_handler as current_handler
from anonbot.internal.processor import ProcessorSource as ProcessorSource
from anonbot.internal.processor import ProcessorManager as ProcessorManager
from anonbot.internal.processor import ProcessorStorage as ProcessorStorage
from anonbot.internal.processor import current_processor as current_processor
from anonbot.internal.processor import DEFAULT_STORAGE_CLASS as DEFAULT_STORAGE_CLASS

__autodoc__ = {
    'Processor': True,
    'processors': True,
    'ProcessorManager': True,
    'ProcessorStorage': True,
    'DEFAULT_STORAGE_CLASS': True
}
