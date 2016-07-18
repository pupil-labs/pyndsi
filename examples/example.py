import logging, time, signal
logging.basicConfig(
    format='%(asctime)s [%(levelname)8s | %(name)-14s] %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

import ndsi
from ndsi.const.event import *

def on_device_event(device, name, event):
    logger.debug('%s %s: %s'%(device, name, repr(event)))

def on_network_event(network, name, event):
    logger.debug('%s %s: %s'%(network, name, repr(event)))
    if event == EVENT_DEVICE_ADDED:
        for uuid in event:
            network.device(uuid, callbacks=(on_device_event,))

n = ndsi.Network(callbacks=(on_network_event,))
n.start()

try:
    while n.running:
        time.sleep(.3)
except (KeyboardInterrupt, SystemExit):
    n.stop()