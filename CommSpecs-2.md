# Network Device Sensor Interface Protocol Specification v2.13

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
    1. Create a `zmq.SUB` socket, connected to
        `notify_endpoint`,
    2. Subscribe to the `sensor`s unique identifier
        (`zmq_setsockopt(<socket>,ZMQ_SUBSCRIBE,<unique identifier>)`) and
        start listening for *update* and *remove* notifications.
    3. Create a `zmq.PUSH` socket, connected to `command_endpoint` (see
        `<attach>` below), send `<refresh_controls>` command.

    - All messages send over these sockets MUST follow the format described below in **Sensor Messages**

### Host Representation Hierarchy
Each host has multiple `sensor` instances. These can be of different types. The "hardware" type includes all device specific controls. Each `sensor` has a list of controls and a unique identifier which is assigned by the **host**. This ID is used for addressing purposes.

```
 pupil-mobile-host ------------     Notifications:          Send/Recv Context:
        |
        +-- <sensor "hardware">     (attach/detach)         WHISPER or SHOUT
        |       +-- <control>       (update/remove)         PUB/SUB socket
        |       |       :
        +-- <sensor "video">        (attach/detach)         WHISPER or SHOUT
        |       +-- <control>       (update/remove)         PUB/SUB socket
        |       |       :
        |       :
        +----------------------
```


### Sensor Messages

All sensor related messages MUST be zeromq multi-part messages with at least
two frames. The first frame MUST include the `sensor`'s unique identifier and
the second the content of a notification or a command. The unique identfier MUST be formatted as an unicode string.

Note: The corresponding value of missing message keys SHALL be handled as `null`.

### Notifications

#### Sequence numbers

All notifications and data messages MUST include a sequence number.
Sequence numbers are cycling `uint32_t` integers.

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
    "data_endpoint"   : <String> // required for sensors that stream data
}

detach = {
    "subject"         : "detach",
    "sensor_uuid"     : <String>
}

sensor_type = "video" XOR "audio" XOR "imu" XOR "hardware" XOR <String>
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
    "error_no"        : <Integer>,
    "error_str"       : <String>
}

control_info = {
    "value"           : <value>,
    "dtype"           : <dtype>,
    "min"             : <number> or null, // minimal value
    "max"             : <number> or null, // maximal value
    "res"             : <number> or null, // resolution or step size
    "def"             : <value>,          // default value
    "caption"         : <String>,
    "readonly"        : <Bool>,
    "map"             : [<str_map>,...]  if <dtype> == "strmapping" XOR
                        [<int_map>,...]  if <dtype> == "intmapping"  XOR
                        null             else
}

str_map = {
    "value"           : <String>
    "caption"         : <String>
}

int_map = {
    "value"           : <Integer>
    "caption"         : <String>
}

sequence_no = <Unsigned Short> // Cycling sequence number
dtype  = "string" XOR "integer" XOR "float" XOR "bool" XOR "strmapping" XOR "intmapping"
value  = <String> XOR <Bool> XOR <number>
number = <Integer> XOR <Float>
```

#### Required controls:

Required controls are pre-defined controls which sensors need to implement in case they support the according action.

###### Streaming

Sensors that support data streaming need to specify an `data_endpoint` in
`<attach>`. It must be specified at anytime -- including when streaming is
turned off. Although, the `data_endpoint` only needs to be reachable when
streaming is turned on.

Additionally, these sensors need to implement the following control:

```javascript
streaming_control_id = "streaming"
streaming_control = {
    "value"           : false,
    "dtype"           : "bool",
    "min"             : null, // minimal value
    "max"             : null, // maximal value
    "res"             : null, // resolution or step size
    "def"             : false,// default value
    "caption"         : "Streaming",
    "readonly"        : false,
    "selector"        : null
}
```

###### Recording

Sensors that support local capture need to implement the following two
controls:

```javascript
local_capture_control_id = "local_capture"
local_capture_control = {
    "value"           : false,
    "dtype"           : "bool",
    "min"             : null, // minimal value
    "max"             : null, // maximal value
    "res"             : null, // resolution or step size
    "def"             : false,// default value
    "caption"         : "Local Capture",
    "readonly"        : false,
    "selector"        : null
}

capture_name_control_id = "capture_session_name"
capture_name_control = {
    "value"           : "Unnamed recording",
    "dtype"           : "string",
    "min"             : null, // minimal value
    "max"             : null, // maximal value
    "res"             : null, // resolution or step size
    "def"             : "Default",// default value
    "caption"         : "Recording name",
    "readonly"        : false,
    "selector"        : null
}
```

### Commands

Commands are `sensor` specific, since they can only be send through the
`sensor` announced **command** socket.

```javascript
command = <refresh_controls> XOR <set_control_value>

refresh_controls = {
    "action"          : "refresh_controls"
}

set_control_value = {
    "action"          : "set_control_value",
    "control_id"      : <String>,
    "value"           : <value>
}
```

## Data

Data messages MUST contain at least three frames:

1. The `sensor`'s unique identifier as unicode string.
2. The data header as 32 bit aligned, little-endian binary
3. The data body as binary

Data header according to `<sensor_type>`:

**video**

```c
typedef struct publish_header {
    uint32_t format_le; // MJPEG, H264, (YUYV, VP8)
    uint32_t width_le;
    uint32_t height_le;
    uint32_t sequence_le;
    int64_t presentation_time_us_le;
    uint32_t data_bytes_le;
    uint32_t reserved_le;
} __attribute__ ((packed)) publish_header_t;

 VIDEO_FRAME_FORMAT_UNKNOWN     = 0     // supported, unknown
 VIDEO_FRAME_FORMAT_YUYV        = 0x01  // supported, YUYV
(VIDEO_FRAME_FORMAT_UYVY        = 0x02)
(VIDEO_FRAME_FORMAT_GRAY8       = 0x03)
(VIDEO_FRAME_FORMAT_BY8         = 0x04)
(VIDEO_FRAME_FORMAT_NV21        = 0x05)
(VIDEO_FRAME_FORMAT_YV12        = 0x06)
(VIDEO_FRAME_FORMAT_I420        = 0x07)
(VIDEO_FRAME_FORMAT_Y16         = 0x08)
(VIDEO_FRAME_FORMAT_RGBP        = 0x09)
(VIDEO_FRAME_FORMAT_M420        = 0x0a)
(VIDEO_FRAME_FORMAT_NV12        = 0x0b)
(VIDEO_FRAME_FORMAT_RGB565      = 0x0c)
(VIDEO_FRAME_FORMAT_RGB         = 0x0d)
(VIDEO_FRAME_FORMAT_BGR         = 0x0e)
(VIDEO_FRAME_FORMAT_RGBX        = 0x0f)
 VIDEO_FRAME_FORMAT_MJPEG       = 0x10  // supported, MJPEG
(VIDEO_FRAME_FORMAT_MPEG2TS     = 0x11)
 VIDEO_FRAME_FORMAT_H264        = 0x12  // supported, H264
 VIDEO_FRAME_FORMAT_VP8         = 0x13  // supported, VP8
(VIDEO_FRAME_FORMAT_YCbCr       = 0x14)
(VIDEO_FRAME_FORMAT_FRAME_H264  = 0x15)
(VIDEO_FRAME_FORMAT_FRAME_VP8   = 0x16)
(VIDEO_FRAME_FORMAT_DV          = 0x17)
```

**audio**:

```c
typedef struct audio_header {
    uint32_t format_le;  // PCM8, PCM16, etc., usually use PCM8 on most of Android devices.
    uint32_t channel_le; // 1 or 2, but most of Android devices just support 1
    uint32_t sequence_le;
    int64_t presentation_time_us_le;
    uint32_t data_bytes_le;
} __attribute__ ((packed)) audio_header;
```

**IMU** and other headers are still to be defined.