from .manager import ProcessorManager as ProcessorManager
from .storage import ProcessorStorage as ProcessorStorage
from .storage import DEFAULT_STORAGE_CLASS as DEFAULT_STORAGE_CLASS

processors = ProcessorManager()

from .processor import Processor as Processor
from .processor import current_bot as current_bot
from .processor import current_event as current_event
from .processor import current_handler as current_handler
from .processor import ProcessorSource as ProcessorSource
from .processor import current_processor as current_processor
