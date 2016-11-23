import logging, zmq, sys, os, json, socket, struct
from uuid import uuid4
logging.basicConfig(
    format='%(asctime)s [%(levelname)8s | %(name)-14s] %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)
logging.getLogger('pyre').setLevel(logging.WARNING)
logging.getLogger('uvc').setLevel(logging.WARNING)

from pyre import Pyre, zhelper, PyreEvent
import uvc

def has_data(socket):
    return socket.get(zmq.EVENTS) & zmq.POLLIN

class Bridge(object):
    """docstring for Bridge"""
    def __init__(self, uvc_id):
        super(Bridge, self).__init__()

        # init capture
        self.cap = uvc.Capture(uvc_id)
        logger.info('Initialised uvc device %s'%self.cap.name)

        # init pyre
        self.network = Pyre(socket.gethostname()+self.cap.name[-4:])
        self.network.start()
        logger.info('Bridging under "%s"'%self.network.name())

        # init sensor sockets
        ctx = zmq.Context()
        generic_url = 'tcp://*:*'
        public_ep   = self.network.endpoint()
        self.note, self.note_url = self.bind(ctx, zmq.PUB , generic_url, public_ep)
        self.data, self.data_url = self.bind(ctx, zmq.PUB , generic_url, public_ep)
        self.cmd , self.cmd_url  = self.bind(ctx, zmq.PULL, generic_url, public_ep)

    def loop(self):
        logger.info('Entering bridging loop...')
        self.network.shout('pupil-mobile', self.sensor_attach_json())
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
            self.network.shout('pupil-mobile', json.dumps({
                'subject'   : 'detach',
                'sensor_uuid': self.network.uuid().hex
            }))
            logger.info('Leaving bridging loop...')

    def publish_frame(self):
        frame = self.cap.get_frame_robust()
        now = int(frame.timestamp*1000000) # timestamp in millisec precision

        jpeg_buffer = frame.jpeg_buffer
        meta_data = struct.pack('<LLLLQLL', 0x10, frame.width, frame.height, frame.index, now, jpeg_buffer.size, 0)
        self.data.send_multipart([self.network.uuid().hex, meta_data, jpeg_buffer])

    def poll_network(self):
        while has_data(self.network.socket()):
            event = PyreEvent(self.network)
            if event.type == 'JOIN' and event.group == 'pupil-mobile':
                self.network.whisper(event.peer_uuid, self.sensor_attach_json())

    def poll_cmd_socket(self):
        while has_data(self.cmd):
            sensor, cmd_str = self.cmd.recv_multipart()
            try:
                cmd = json.loads(cmd_str)
            except Exception as e:
                logger.debug('Could not parse received cmd: %s'%cmd_str)
            else:
                logger.debug('Received cmd: %s'%cmd)

    def __del__(self):
        self.note.close()
        self.data.close()
        self.cmd.close()
        self.network.stop()

    def sensor_attach_json(self):
        sensor = {
            "subject"         : "attach",
            "sensor_name"     : self.cap.name,
            "sensor_uuid"     : self.network.uuid().hex,
            "sensor_type"     : 'video',
            "notify_endpoint" : self.note_url,
            "command_endpoint": self.cmd_url,
            "data_endpoint"   : self.data_url
        }
        return json.dumps(sensor)


    def bind(self, ctx, sock_type, url, public_ep):
        sock = ctx.socket(sock_type)
        sock.bind(url)
        ep = sock.last_endpoint
        port = ep.split(':')[-1]
        public_ep.split(':')[-1]
        public_addr = public_ep.split(':')[:-1]
        return sock, ':'.join(public_addr+[port])

if __name__ == '__main__':
    uuid = None
    dev_list =  uvc.Device_List()
    for dev in dev_list:
        uuid = dev['uid']
        if uvc.is_accessible(uuid):
            break

    if uuid: Bridge(uuid).loop()
