# Network Device Sensor Interface Protocol Specification v2.8

Status: draft


Network Device Sensor Interface protocol specifies the communication
between *Pupil Mobile* and the *Network Device Sensor Interface*.


The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://tools.ietf.org/html/rfc2119).

## Control

### Host vs Clients

**Hosts** (e.g. Android app):

- **Hosts** SHOULD NOT join `pupil-mobile`.
- **Hosts** MUST SHOUT `<attach>` and `<detach>` notifications to
`pupil-mobile`.
- **Hosts** MUST WHISPER all currently available `sensor`s as a series
of `<attach>` notifications when a **client** joins `pupil-mobile`.
- **Hosts** MUST open at least one socket for each following type:
    - **Notify** `zmq.PUB` socket, publishes `sensor` specific control
    notifications (`update` and `remove`), randomly choosen port
    - **Command** `zmq.PULL` socket, receives `sensor` specific commands,
    randomly choosen port
    - **Data** `zmq.PUB` socket, publishes stream data, format depends on
    `sensor` type, randomly choosen port
- All messages send over these sockets MUST follow the format described below in **Sensor Messages**
- **Hosts** MUST listen for messages on the **command** socket.
- **Hosts** MUST publish all `control` state changes over its **notify**
socket.
- **Hosts** MUST respond to `<refresh_controls>` by publishing all available
`control` states as a series of `<control_update>`

**Clients** (e.g. the `ndsi` library)

- **Clients** MUST join `pupil-mobile`.
- **Clients** MUST listen to incoming SHOUT and WHISPER messages.
    - Messages including invalid `json` SHOULD be dropped (silently).
- **Clients** SHOULD maintain a list of available `sensor`s including
    their static information (this includes especially the unique identifier
    defined by the **host**, see **Sensor Messages** below).
- To receive control updates of a specific `sensor`, **Clients** MUST:
    1) Create a `zmq.SUB` socket, connected to
        `notify_endpoint`,
    2) Subscribe to the `sensor`s unique identifier
        (`zmq_setsockopt(<socket>,ZMQ_SUBSCRIBE,<unique identifier>)`) and
        start listening for *update* and *remove* notifications.
    3) Create a `zmq.PUSH` socket, connected to `command_endpoint` (see
        `<attach>` below), send `<refresh_controls>` command.

    - All messages send over these sockets MUST follow the format described below in **Sensor Messages**

### Host Representation Hierarchy
Each host has multiple `sensor` instances, including a reserved `sensor` named
"hardware". It includes all device specific controls. Each `sensor` has a list
of controls and a unique identifier which is assigned by the **host**. This ID
is used for addressing purposes.

```
 pupil-mobile-host ------------     Notifications:          Send/Recv Context:
        |
        +-- <sensor "hardware">     (attach/detach)         WHISPER or SHOUT
        |       +-- <control>       (update/remove)         PUB/SUB socket
        |       |       :
        +-- <sensor>                (attach/detach)         WHISPER or SHOUT
        |       +-- <control>       (update/remove)         PUB/SUB socket
        |       |       :
        |       :
        +----------------------
```


### Sensor Messages

All sensor related messages MUST be zeromq multi-part messages with at least
two frames. The first frame MUST include the `sensor`'s unique identifier and
the second the content of a notification or a command.

### Notifications

#### Sequence numbers

All notifications and data messages MUST include a sequence number.
Sequence numbers are cycling, unsigned 2-octet (short) integers `[0 - 65535]`.

Sequence number counters are per sensor and per message type. This means that
each `sensor` needs to maintain a counter for notifications and an other
counter for its data messages. Sequence numbers can have an arbitrary start but MUST be strictly increasing afterwards.

`<attach>` and `<detach>` notifications already include implicit sequence numbers through the [ZRE protocol specification](http://rfc.zeromq.org/spec:36/ZRE/#tcp-protocol-grammar) and therefore do not need an own sequence number.

`<control_update>`, `<control_remove>`, and `<error>` include a `seq` field
which MUST contain the sequence number of the message.

**Clients** SHOULD use the sequence number to detect loss of messages.

#### Send/Recv Context: WHISPER or SHOUT

```javascript
notification = <attach> XOR <detach>

attach = {
    "subject"         : "attach",
    "sensor_name"     : <String>,
    "sensor_uuid"     : <String>,
    "sensor_type"     : <sensor_type>,
    "notify_endpoint" : <String>,
    "command_endpoint": <String>,
    "data_endpoint"   : <String> // optional
}

detach = {
    "subject"         : "detach",
    "sensor_uuid"     : <String>
}

sensor_type = "video" XOR "audio" XOR "imu" XOR <String>
```

Endpoints are strings which are used for zmq sockets and follow the `<protocol>://<address>:<port>` scheme.

#### Send/Recv Context: PUB/SUB socket

`sensor` specific notifications only, since they can only be received through
subscribing to the `sensor` announced **notify** socket.

```javascript
notification = <control_update> XOR <control_remove> XOR <error>

control_update = {
    "subject"         : "update",
    "control_id"      : <String>,
    "seq"             : <sequence_no>,
    "changes"         : <Dict control_info>
}

control_remove = {
    "subject"         : "remove",
    "control_id"      : <String>,
    "seq"             : <sequence_no>
}

error = {
    "subject"         : "error",
    "control_id"      : <String> XOR null,
    "seq"             : <sequence_no>,
    "info"            : <Dict error_info>
}

control_info = {
    "value"           : <value>,
    "dtype"           : <dtype>,
    "min"             : <number> or null, // minimal value
    "max"             : <number> or null, // maximal value
    "res"             : <number> or null, // resolution or step size
    "def"             : <value>,          // default value
    "caption"         : <String>,
    "selector"        : [<selector_desc>,...] XOR [<bitmap_desc>,...] XOR null
}

error_info = {
    "error_no"        : <Integer>,
    "error_id"        : <String>
}

selector_desc = {
    "id"              : <String>
    "value"           : <String>
    "caption"         : <String>
}

bitmap_desc = {
    "id"              : <String>
    "value"           : <Integer>
    "caption"         : <String>
}

sequence_no = <Unsigned Short> // Cycling sequence number
dtype  = "string" XOR "integer" XOR "float" XOR "bool" XOR "selector"
value  = <String> XOR <Bool> XOR <number> XOR null
number = <Integer> XOR <Float>
```

### Commands

Commands are `sensor` specific, since they can only be send through the
`sensor` announced **command** socket.

```javascript
command = <refresh_controls> XOR <set_control_value> XOR <sensor_cmd>

refresh_controls = {
    "action"          : "refresh_controls"
}

set_control_value = {
    "action"          : "set_control_value",
    "control_id"      : <String>,
    "value"           : <value>
}

sensor_cmd = {
    "action": "stream_on" XOR "stream_off" XOR "record_on" XOR "record_off"
}
```

## Data

Data messages MUST contain at least three frames:

1) The `sensor`'s unique identifier.
2) A json decoded `<meta_data>` object.
3) A raw byte buffer.

`<meta_data>` MUST contain at least the following fields:

```javascript
meta_data = {
    "seq"             : <sequence_no>,
    "timestamp"       : <Double>
}
```

Depending on the `<sensor_type>` the **host** SHOULD add relevant
meta information to the `<meta_data>` object.
