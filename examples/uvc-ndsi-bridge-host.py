import hashlib
import json
import logging
import socket
import struct
import time

import uvc
import zmq
from pyre import Pyre

logging.basicConfig(
    format="%(asctime)s [%(levelname)8s | %(name)-14s] %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)
logging.getLogger("pyre").setLevel(logging.WARNING)
logging.getLogger("uvc").setLevel(logging.WARNING)

sequence_limit = 2**32 - 1

GROUP = "pupil-mobile-v3"


def has_data(socket):
    return socket.get(zmq.EVENTS) & zmq.POLLIN


class Bridge:
    """docstring for Bridge"""

    def __init__(self, uvc_id):
        super().__init__()

        self.data_seq = 0
        self.note_seq = 0

        # init capture
        self.cap = uvc.Capture(uvc_id)
        logger.info(f"Initialised uvc device {self.cap.name}")

        # init pyre
        self.network = Pyre(socket.gethostname() + self.cap.name[-4:])
        self.network.join(GROUP)
        self.network.start()
        logger.info(f'Bridging under "{self.network.name()}"')

        # init sensor sockets
        ctx = zmq.Context()
        generic_url = "tcp://*:*"
        public_ep = self.network.endpoint()
        self.note, self.note_url = self.bind(ctx, zmq.PUB, generic_url, public_ep)
        self.data, self.data_url = self.bind(
            ctx, zmq.PUB, generic_url, public_ep, set_hwm=1
        )
        self.cmd, self.cmd_url = self.bind(ctx, zmq.PULL, generic_url, public_ep)

    def loop(self):
        logger.info("Entering bridging loop...")
        self.network.shout(GROUP, self.sensor_attach_json().encode())
        try:
            while True:
                self.poll_network()
                self.poll_cmd_socket()
                self.publish_frame()

        except KeyboardInterrupt:
            pass
        except Exception:
            import traceback

            traceback.print_exc()
        finally:
            self.network.shout(
                GROUP,
                json.dumps(
                    {"subject": "detach", "sensor_uuid": self.network.uuid().hex}
                ).encode(),
            )
            logger.info("Leaving bridging loop...")

    def publish_frame(self):
        frame = self.cap.get_frame_robust()
        now = time.time()
        index = self.data_seq
        self.data_seq += 1
        self.data_seq %= sequence_limit

        jpeg_buffer = frame.jpeg_buffer
        m = hashlib.md5(jpeg_buffer)
        lower_end = int(m.hexdigest(), 16) % 0x100000000
        meta_data = struct.pack(
            "<LLLLdLL",
            0x10,
            frame.width,
            frame.height,
            index,
            now,
            jpeg_buffer.size,
            lower_end,
        )
        self.data.send_multipart(
            [self.network.uuid().hex.encode(), meta_data, jpeg_buffer]
        )

    def poll_network(self):
        for event in self.network.recent_events():
            if event.type == "JOIN" and event.group == GROUP:
                self.network.whisper(
                    event.peer_uuid, self.sensor_attach_json().encode()
                )

    def poll_cmd_socket(self):
        while has_data(self.cmd):
            sensor, cmd_str = self.cmd.recv_multipart()
            try:
                cmd = json.loads(cmd_str.decode())
            except Exception as e:
                logger.debug(f"Could not parse received cmd: {cmd_str}")
            else:
                logger.debug(f"Received cmd: {cmd}")
                if cmd.get("action") == "refresh_controls":
                    self.publish_controls()
                elif cmd.get("action") == "set_control_value":
                    val = cmd.get("value", 0)
                    if cmd.get("control_id") == "CAM_RATE":
                        self.cap.frame_rate = self.cap.frame_rates[val]
                    elif cmd.get("control_id") == "CAM_RES":
                        self.cap.frame_size = self.cap.frame_sizes[val]
                    self.publish_controls()

    def __del__(self):
        self.note.close()
        self.data.close()
        self.cmd.close()
        self.network.stop()

    def publish_controls(self):
        self.note.send_multipart(
            [self.network.uuid().hex.encode(), self.frame_size_control_json().encode()]
        )
        self.note.send_multipart(
            [self.network.uuid().hex.encode(), self.frame_rate_control_json().encode()]
        )

    def sensor_attach_json(self):
        sensor = {
            "subject": "attach",
            "sensor_name": self.cap.name,
            "sensor_uuid": self.network.uuid().hex,
            "sensor_type": "video",
            "notify_endpoint": self.note_url,
            "command_endpoint": self.cmd_url,
            "data_endpoint": self.data_url,
        }
        return json.dumps(sensor)

    def frame_size_control_json(self):
        index = self.note_seq
        self.note_seq += 1
        self.note_seq %= sequence_limit
        curr_fs = self.cap.frame_sizes.index(self.cap.frame_size)
        return json.dumps(
            {
                "subject": "update",
                "control_id": "CAM_RES",
                "seq": index,
                "changes": {
                    "value": curr_fs,
                    "dtype": "intmapping",
                    "min": None,
                    "max": None,
                    "res": None,
                    "def": 0,
                    "caption": "Resolution",
                    "readonly": False,
                    "map": [
                        {"value": idx, "caption": "{:d}x{:d}".format(*fs)}
                        for idx, fs in enumerate(self.cap.frame_sizes)
                    ],
                },
            }
        )

    def frame_rate_control_json(self):
        index = self.note_seq
        self.note_seq += 1
        self.note_seq %= sequence_limit
        curr_fr = self.cap.frame_rates.index(self.cap.frame_rate)
        return json.dumps(
            {
                "subject": "update",
                "control_id": "CAM_RATE",
                "seq": index,
                "changes": {
                    "value": curr_fr,
                    "dtype": "intmapping",
                    "min": None,
                    "max": None,
                    "res": None,
                    "def": 0,
                    "caption": "Frame Rate",
                    "readonly": False,
                    "map": [
                        {"value": idx, "caption": f"{fr:.1f} Hz"}
                        for idx, fr in enumerate(self.cap.frame_rates)
                    ],
                },
            }
        )

    def bind(self, ctx, sock_type, url, public_ep, set_hwm=None):
        sock = ctx.socket(sock_type)
        if set_hwm:
            sock.set_hwm(set_hwm)
        sock.bind(url)
        ep = sock.last_endpoint.decode()
        port = ep.split(":")[-1]
        public_ep.split(":")[-1]
        public_addr = public_ep.split(":")[:-1]
        return sock, ":".join(public_addr + [port])


if __name__ == "__main__":
    uuid = None
    dev_list = uvc.Device_List()
    for dev in dev_list:
        uuid = dev["uid"]
        if uvc.is_accessible(uuid):
            break
    if uuid:
        Bridge(uuid).loop()
