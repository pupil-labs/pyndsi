import logging, time, signal
logging.basicConfig(format='%(asctime)s [%(levelname)8s | %(name)-14s] %(message)s', datefmt='%H:%M:%S', level=logging.DEBUG)
logger = logging.getLogger(__name__)

import ndsi

n = ndsi.Network()
n.start()

try:
    while n.running:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    n.stop()