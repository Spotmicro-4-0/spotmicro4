from spotmicroai.utilities.log import Logger
from spotmicroai.singleton import Singleton

log = Logger().setup_logger('System')

class General(metaclass=Singleton):

    def __init__(self):

        try:
            log.debug('Loading general...')

        except Exception as e:
            log.error('Problem while loading the general singleton', e)

    def maprange(self, a, b, s):
        (a1, a2), (b1, b2) = a, b
        return b1 + ((s - a1) * (b2 - b1) / (a2 - a1))
