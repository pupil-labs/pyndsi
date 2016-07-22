# Network Device Sensor Interface Protocol Specification v2.5

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://tools.ietf.org/html/rfc2119).

## Control

### Host vs Clients

**Hosts** (e.g. Android app):

- **Hosts** SHOULD NOT join `pupil-mobile`.
- **Hosts** MUST SHOUT `<attach>` and `<detach>` notifications to
`pupil-mobile`.
- **Hosts** MUST WHISPER all currently available `sensor`s as a series
of `<attach>` notifications when a **client** joins `pupil-mobile`.
- **Hosts** MUST open following sockets for each `sensor`:
    - **Notify** `zmq.PUB` socket, publishes `sensor` specific control
    notifications (`update` and `remove`), randomly choosen port
    - **Command** `zmq.PULL` socket, receives `sensor` specific commands,
    randomly choosen port
- **Hosts** MAY open following sockets for each `sensor`:
    - **Data** `zmq.PUB` socket, publishes stream data, format depends on
    `sensor` type, randomly choosen port
- **Hosts** MUST listen for messages on the **command** socket.
- **Hosts** MUST publish all `control` state changes over its **notify**
socket.
- **Hosts** MUST respond to `<refresh_controls>` by publishing all available
`control` states as a series of `<control_update>`

**Clients** (e.g. `ndsi` applications)

- **Clients** MUST join `pupil-mobile`.
- **Clients** MUST listen to incoming SHOUT and WHISPER messages.
    - Messages including invalid `json` SHOULD be dropped (silently).
- **Clients** SHOULD maintain a list of available `sensor`s including
    their static information (see above). `sensor`s are uniquely
    identifiable through a combination of `sensor_name` and **host**
    uuid (e.g. `<sensor name>@<host uuid>`).
- To receive control updates, **Clients** MUST:
    1) Create a `zmq.SUB` socket, connected to
    `notify_endpoint`,
    2) Subscribe to all messages (`zmq_setsockopt(<socket>,ZMQ_SUBSCRIBE,'')`) and start listening for *update* and *remove* notifications.
    2) Create a `zmq.PUSH` socket, connected to `command_endpoint`,
    send `<refresh_controls>` command.

### Host Representation Hierarchy
Each host has multiple `sensor` instances, including a reserved `sensor` named
"hardware". It includes all device specific controls. Each `sensor` has a list
of controls.

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

### Notifications

#### Send/Recv Context: WHISPER or SHOUT

```javascript
notification = <attach> XOR <detach>

attach = {
    "subject"         : "attach",
    "sensor_name"     : <String>,
    "sensor_type"     : <String>,
    "notify_endpoint" : <String>,
    "command_endpoint": <String>,
    "data_endpoint"   : <String> // optional
}

detach = {
    "subject"         : "detach",
    "sensor_name"     : <String>
}
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
    "changes"         : <Dict control_info>
}

control_remove = {
    "subject"         : "remove",
    "control_id"      : <String>
}

error = {
    "subject"         : "error",
    "control_id"      : <String> XOR null,
    "info"            : <Dict error_info>
}

control_info = {
    "value"           : <value>,
    "dtype"           : <dtype>,
    "min"             : <number> or null,
    "max"             : <number> or null,
    "def"             : <value>,
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

*Work in progress.*