import logging
import signal
import sys
import time

logging.basicConfig(
    format="%(asctime)s [%(levelname)8s | %(name)-14s] %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)
logging.getLogger("pyre").setLevel(logging.WARNING)

import ndsi

sensors = {}


def on_sensor_event(sensor, event):
    logger.debug(
        "{} [{}] {} {}".format(
            sensor, event["seq"], event["subject"], event["control_id"]
        )
    )


def on_network_event(network, event):
    if event["subject"] == "attach":
        sensor = network.sensor(event["sensor_uuid"], callbacks=(on_sensor_event,))
        logger.debug("Linking sensor %s..." % sensor)
        sensors[event["sensor_uuid"]] = sensor
    if event["subject"] == "detach":
        logger.debug("Unlinking sensor %s..." % event["sensor_uuid"])
        sensors[event["sensor_uuid"]].unlink()
        del sensors[event["sensor_uuid"]]


n = ndsi.Network(callbacks=(on_network_event,))
n.start()

try:
    while n.running:
        if n.has_events:
            n.handle_event()
        for s in sensors.values():
            if s.has_notifications:
                s.handle_notification()
        time.sleep(0.1)
except (KeyboardInterrupt, SystemExit):
    n.stop()
    sys.exit()
