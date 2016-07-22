import logging, time, signal
logging.basicConfig(
    format='%(asctime)s [%(levelname)8s | %(name)-14s] %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)
logging.getLogger('pyre').setLevel(logging.WARNING)

import ndsi

sensors = {}

def on_sensor_event(sensor, event):
    logger.debug('%s: %s'%(sensor, repr(event)))

def on_network_event(network, event):
    if event['subject'] == 'attach':
        sensor = network.sensor(event['sensor_id'], callbacks=(on_sensor_event,))
        logger.debug('Linking sensor %s...'%sensor)
        sensors[event['sensor_id']] = sensor
    if event['subject'] == 'detach':
        logger.debug('Unlinking sensor %s...'%event['sensor_id'])
        sensors[event['sensor_id']].unlink()
        del sensors[event['sensor_id']]

n = ndsi.Network(callbacks=(on_network_event,))
n.start()

try:
    while n.running:
        if n.has_events:
            n.handle_event()
        for s in sensors.values():
            if s.has_notifications:
                s.handle_notification()
        time.sleep(.1)
except (KeyboardInterrupt, SystemExit):
    n.stop()