import anonbot
from anonbot.adapter.satori import Adapter

anonbot.init('config.yml')
anonbot.get_driver().register_adapter(Adapter)
anonbot.load_plugins('plugins')

anonbot.run()
