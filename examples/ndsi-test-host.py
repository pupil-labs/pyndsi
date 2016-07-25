from pyre import Pyre, zhelper, PyreEvent
import zmq, time, json, logging, traceback as tb, uuid, sys

logging.basicConfig(
    format='%(asctime)s [%(levelname)8s | %(name)-14s] %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)
logging.getLogger('pyre').setLevel(logging.WARNING)

def make_control(value,dtype,min_v,max_v,def_v,cap,selector):
    return {
        "value"   : value,
        "dtype"   : dtype,
        "min"     : min_v,
        "max"     : max_v,
        "def"     : def_v,
        "caption" : cap,
        "selector": selector
    }

class NDSITestHost(object):
    """docstring for NDSITestHost"""
    def __init__(self):
        super(NDSITestHost, self).__init__()
        self.pipe = None
        self.state = {}
        self.sequences = {}

    @property
    def running(self):
        return bool(self.pipe)

    def __str__(self):
        return '<%s running=%s>'%(type(self).__name__, self.running)

    def start(self, initial_state):
        ctx = zmq.Context()
        self.pipe = zhelper.zthread_fork(ctx, self.host_task)
        for sensor in initial_state:
            time.sleep(1)
            self.attach(sensor)

    def stop(self):
        self.pipe.send('$TERM')
        while self.pipe:
            time.sleep(.1)

    def attach(self,sensor):
        self.pipe.send_multipart(['ATTACH SENSOR', json.dumps(sensor)])

    def detach(self,sensor_name):
        self.pipe.send_multipart(['DETACH SENSOR', sensor_name])

    def set_control(self, sensor_name, control_id, control):
        self.pipe.send_multipart(['TELL SENSOR', sensor_name, 'SET CONTROL', control_id, json.dumps(control)])

    def whisper_sensor_state(self, node, peer_uuid):
        for sensor in self.state.values():
            notification = sensor.copy()
            notification['subject'] = 'attach'
            node.whisper(peer_uuid, json.dumps(notification))

    def host_task(self, ctx, pipe):
        sensor_pipes = {}
        n = Pyre("TestHost")
        n.start()
        poller = zmq.Poller()
        poller.register(pipe, zmq.POLLIN)
        poller.register(n.socket(), zmq.POLLIN)

        def _attach_sensor(sensor):
            logger.debug('Attaching <%s>...', sensor)
            sp = zhelper.zthread_fork(ctx, self.sensor_task, n, sensor)
            sensor = sp.recv_pyobj()
            name = sensor['sensor_name']
            sensor_pipes[name] = sp
            self.sequences[name] = 0
            poller.register(sp, zmq.POLLIN)
            self.state.update({name: sensor.copy()})
            sensor['subject'] = 'attach'
            n.shout('pupil-mobile', json.dumps(sensor))

        def _detach_sensor(sensor_name,send_term=False):
            logger.debug('Detaching %s...', sensor_name)
            if not send_term:
                sensor_pipes[sensor_name].send('$TERM')
                sensor_pipes[sensor_name].close()
            del sensor_pipes[sensor_name]
            del self.state[sensor_name]
            del self.sequences[sensor_name]
            n.shout('pupil-mobile', json.dumps({
                "subject"     : "detach",
                "sensor_name" : sensor_name
            }))

        try:
            while(True):
                items = dict(poller.poll())
                if n.socket() in items:
                    event = PyreEvent(n)
                    if event.type == 'JOIN' and event.group == 'pupil-mobile':
                        self.whisper_sensor_state(n, event.peer_uuid)

                elif pipe in items:
                    msg = pipe.recv_multipart()
                    cmd = msg.pop(0)
                    if cmd == '$TERM':
                        for sp in sensor_pipes.values():
                            sp.send('$TERM')
                        break
                    elif cmd == 'ATTACH SENSOR':
                        sensor = msg.pop(0)
                        _attach_sensor(sensor)
                    elif cmd == 'DETACH SENSOR':
                        sensor_name = msg.pop(0)
                        _detach_sensor(sensor_name)
                    elif cmd == 'TELL SENSOR':
                        # forward message
                        sensor_name = msg.pop(0)
                        if sensor_name in sensor_pipes:
                            logger.debug('Forwarding to %s...'%sensor_name)
                            sp = sensor_pipes[sensor_name]
                            sp.send_multipart(msg)
                        else:
                            logger.warning('Could not tell %s.'%sensor_name)
                else:
                    for sensor_name in sensor_pipes.keys():
                        sp = sensor_pipes[sensor_name]
                        if sp in items:
                            sp_cmd = sp.recv()
                            if sp_cmd == 'STOP':
                                _detach_sensor(sensor_name,send_term=True)


        except Exception:
            tb.print_exc()
        finally:
            n.stop()
            self.pipe = None

    def sensor_task(self, ctx, pipe, network, sensor):
        sensor = json.loads(sensor)
        generic_url = 'tcp://*:*'
        try:
            controls = sensor['controls']
            del sensor['controls']
        except KeyError:
            controls = {}

        note, note_url = self.bind_socket(ctx, zmq.PUB , generic_url, network)
        cmd , cmd_url  = self.bind_socket(ctx, zmq.PULL, generic_url, network)

        sensor.update({
            'notify_endpoint': note_url,
            'command_endpoint': cmd_url
        })

        poller = zmq.Poller()
        poller.register(pipe, zmq.POLLIN)
        poller.register(cmd, zmq.POLLIN)

        logger.debug('Started sensor <%s>'%repr(sensor))

        pipe.send_pyobj(sensor)
        this_sensor = sensor['sensor_name']

        def sensor_publish_control(control_id, changes=None):
            logger.debug('Publishing control change for <%s>'%control_id)
            changes = changes or controls[control_id]
            seq = self.sequences[this_sensor]
            self.sequences[this_sensor] += 1
            self.sequences[this_sensor] %= 65535
            serial = json.dumps({
                'subject'   : 'update',
                'control_id': control_id,
                'changes'   : changes,
                'seq'       : seq
            })
            note.send(serial)

        def sensor_set_control(control_id, control):
            controls.update({control_id: control})
            sensor_publish_control(control_id, changes=control)

        def sensor_set_control_value(control_id, value):
            controls[control_id]['value'] = value
            sensor_publish_control(control_id, changes={'value': value})

        def sensor_publish_error(error, control_id=None):
            seq = self.sequences[this_sensor]
            self.sequences[this_sensor] += 1
            self.sequences[this_sensor] %= 65535
            serial = json.dumps({
                'subject'   : 'error',
                'control_id': control_id,
                'info'      : error,
                'seq'       : seq
            })
            note.send(serial)

        try:
            while(True):
                items = dict(poller.poll())
                if cmd in items:
                    msg = cmd.recv()
                    try:
                        client_cmd = json.loads(msg)
                        client_cmd['action']
                    except:
                        logger.warning('Invalid message: %s', msg)
                    else:
                        logger.debug('%s received command: %s'%(sensor['sensor_name'],repr(client_cmd)))
                        if client_cmd['action'] == 'refresh_controls':
                            for cid in controls:
                                sensor_publish_control(cid)
                        elif client_cmd['action'] == 'set_control_value':
                            try:
                                sensor_set_control_value(client_cmd['control_id'], client_cmd['value'])
                            except KeyError:
                                logger.warning('Malformed command: %s'%e)
                                sensor_publish_error({'error_no': -1, 'error_id': 'Malformed command'})
                        else:
                            raise NotImplementedError('<%s> is not implemented'%client_cmd['action'])

                if pipe in items:
                    msg = pipe.recv_multipart()
                    sensor_cmd = msg.pop(0)
                    if sensor_cmd == '$TERM':
                        break
                    elif sensor_cmd == 'SET CONTROL':
                        control_id = msg.pop(0)
                        json_msg = msg.pop(0)
                        ctrl = json.loads(json_msg)
                        sensor_set_control(control_id, ctrl)

        except Exception:
            tb.print_exc()
        finally:
            pipe.send('STOP')
            logger.debug('Shutting down sensor <%s>'%repr(sensor))

    def bind_socket(self, ctx, sock_type, url, n):
        sock = ctx.socket(sock_type)
        sock.bind(url)
        ep = sock.last_endpoint
        port = ep.split(':')[-1]
        public_ep = n.endpoint()
        public_ep.split(':')[-1]
        public_addr = public_ep.split(':')[:-1]
        return sock, ':'.join(public_addr+[port])

if __name__ == '__main__':
    config = [
        {
            'sensor_name': 'sensor0',
            'sensor_type': 'TEST',
            'controls': {
                'ctrl_id0': make_control('0','float','0','1','0','TC0',None),
                'ctrl_id1': make_control('0','integer','0','100','0','TC1',None),
            }
        },
        {
            'sensor_name': 'sensor1',
            'sensor_type': 'TEST'
        }
    ]
    host = NDSITestHost()
    host.start(config)
    logger.debug(host)

    time.sleep(5)
    additional_controls = {
        'ctrl_id2': make_control('0','float','0','1','0','TC0',None),
        'ctrl_id3': make_control('0','integer','0','100','0','TC1',None),
    }
    for cid, ctrl in additional_controls.iteritems():
        host.set_control('sensor1', cid, ctrl)

    try:
        while host.running:
            time.sleep(.3)
    except KeyboardInterrupt as e:
        host.stop()
    finally:
        logger.debug(host)
        sys.exit()