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

    def detach(self,sensor_uuid):
        self.pipe.send_multipart(['DETACH SENSOR', sensor_uuid])

    def set_control(self, sensor_uuid, control_id, control):
        self.pipe.send_multipart(['TELL SENSOR', sensor_uuid, 'SET CONTROL', control_id, json.dumps(control)])

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
            name = sensor['sensor_uuid']
            sensor_pipes[name] = sp
            self.sequences[name] = 0
            poller.register(sp, zmq.POLLIN)
            self.state.update({name: sensor.copy()})
            sensor['subject'] = 'attach'
            n.shout('pupil-mobile', json.dumps(sensor))

        def _detach_sensor(sensor_uuid,send_term=False):
            logger.debug('Detaching %s...', sensor_uuid)
            if not send_term:
                sensor_pipes[sensor_uuid].send('$TERM')
                sensor_pipes[sensor_uuid].close()
            del sensor_pipes[sensor_uuid]
            del self.state[sensor_uuid]
            del self.sequences[sensor_uuid]
            n.shout('pupil-mobile', json.dumps({
                "subject"     : "detach",
                "sensor_uuid" : sensor_uuid
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
                        sensor_uuid = msg.pop(0)
                        _detach_sensor(sensor_uuid)
                    elif cmd == 'TELL SENSOR':
                        # forward message
                        sensor_uuid = msg.pop(0)
                        if sensor_uuid in sensor_pipes:
                            logger.debug('Forwarding to %s...'%sensor_uuid)
                            sp = sensor_pipes[sensor_uuid]
                            sp.send_multipart(msg)
                        else:
                            logger.warning('Could not tell %s.'%sensor_uuid)
                else:
                    for sensor_uuid in sensor_pipes.keys():
                        sp = sensor_pipes[sensor_uuid]
                        if sp in items:
                            sp_cmd = sp.recv()
                            if sp_cmd == 'STOP':
                                _detach_sensor(sensor_uuid,send_term=True)


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
        this_sensor_uuid = sensor['sensor_uuid']

        def sensor_publish_control(control_id, changes=None):
            logger.debug('Publishing control change for <%s>'%control_id)
            changes = changes or controls[control_id]
            seq = self.sequences[this_sensor_uuid]
            self.sequences[this_sensor_uuid] += 1
            self.sequences[this_sensor_uuid] %= 65535
            serial = json.dumps({
                'subject'   : 'update',
                'control_id': control_id,
                'changes'   : changes,
                'seq'       : seq
            })
            note.send_multipart([str(this_sensor_uuid),serial])

        def sensor_set_control(control_id, control):
            controls.update({control_id: control})
            sensor_publish_control(control_id, changes=control)

        def sensor_set_control_value(control_id, value):
            controls[control_id]['value'] = value
            sensor_publish_control(control_id, changes={'value': value})

        def sensor_publish_error(error, control_id=None):
            seq = self.sequences[this_sensor_uuid]
            self.sequences[this_sensor_uuid] += 1
            self.sequences[this_sensor_uuid] %= 65535
            serial = json.dumps({
                'subject'   : 'error',
                'control_id': control_id,
                'info'      : error,
                'seq'       : seq
            })
            note.send_multipart([str(this_sensor_uuid),serial])

        try:
            while(True):
                items = dict(poller.poll())
                if cmd in items:
                    msg = cmd.recv_multipart()
                    try:
                        if msg[0] != this_sensor_uuid:
                            raise ValueError('Message was destined for %s but was recieved by %s'%(msg[0],this_sensor_uuid))
                        client_cmd = json.loads(msg[1])
                        client_cmd['action']
                    except:
                        logger.warning('Sensor %s: Invalid message: %s'%(this_sensor_uuid, msg))
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
    uuid_no1 = uuid.uuid4().hex
    uuid_no2 = uuid.uuid4().hex
    config = [
        {
            'sensor_name': 'sensor0',
            'sensor_uuid': uuid_no1,
            'sensor_type': 'TEST',
            'controls': {
                'ctrl_id0': make_control('0','float','0','1','0','TC0',None),
                'ctrl_id1': make_control('0','integer','0','100','0','TC1',None),
            }
        },
        {
            'sensor_name': 'sensor1',
            'sensor_uuid': uuid_no2,
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
        host.set_control(uuid_no2, cid, ctrl)

    try:
        while host.running:
            time.sleep(.3)
    except KeyboardInterrupt as e:
        host.stop()
    finally:
        logger.debug(host)
        sys.exit()