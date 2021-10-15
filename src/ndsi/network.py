"""
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2015  Pupil Labs

 Distributed under the terms of the CC BY-NC-SA License.
 License details are in the file LICENSE, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
"""

import abc
import collections
import functools
import itertools
import json as serial
import logging
import sys
import time
import traceback as tb
import typing

import zmq
from pyre import Pyre, PyreEvent, zhelper

from ndsi import __protocol_version__
from ndsi.formatter import DataFormat
from ndsi.sensor import Sensor, SensorType

logger = logging.getLogger(__name__)


NetworkEvent = typing.Mapping[str, typing.Any]


NetworkEventCallback = typing.Callable[[typing.Any, NetworkEvent], None]


NetworkSensor = typing.Mapping[str, typing.Any]


class NetworkInterface(abc.ABC):
    """
    Public interface for a Network-like object.
    """

    @property
    @abc.abstractmethod
    def has_events(self) -> bool:
        pass

    @property
    @abc.abstractmethod
    def running(self) -> bool:
        pass

    @property
    @abc.abstractmethod
    def sensors(self) -> typing.Mapping[str, NetworkSensor]:
        pass

    @property
    @abc.abstractmethod
    def callbacks(self) -> typing.Iterable[NetworkEventCallback]:
        pass

    @callbacks.setter
    @abc.abstractmethod
    def callbacks(self, value: typing.Iterable[NetworkEventCallback]):
        pass

    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def whisper(self, peer, msg_p):
        """Send message to single peer, specified as a UUID string"""
        pass

    @abc.abstractmethod
    def rejoin(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def handle_event(self):
        pass

    @abc.abstractmethod
    def sensor(
        self, sensor_uuid: str, callbacks: typing.Iterable[NetworkEventCallback] = ()
    ) -> Sensor:
        pass


class _NetworkNode(NetworkInterface):
    """
    Communication node

    Creates Pyre node and handles all communication.
    """

    def __init__(
        self, format: DataFormat, context=None, name=None, headers=(), callbacks=()
    ):
        self._name = name
        self._format = format
        self._headers = headers
        self._pyre_node = None
        self._context = context or zmq.Context()
        self._sensors_by_host = {}
        self._callbacks = [self._on_event] + list(callbacks)

    # Public NetworkInterface API

    @property
    def has_events(self) -> bool:
        return self.running and self._pyre_node.socket().get(zmq.EVENTS) & zmq.POLLIN

    @property
    def running(self) -> bool:
        return bool(self._pyre_node)

    @property
    def sensors(self) -> typing.Mapping[str, NetworkSensor]:
        sensors = {}
        for sensor in self._sensors_by_host.values():
            sensors.update(sensor)
        return sensors

    @property
    def callbacks(self) -> typing.Iterable[NetworkEventCallback]:
        return self._callbacks

    @callbacks.setter
    def callbacks(self, value: typing.Iterable[NetworkEventCallback]):
        self._callbacks = value

    def start(self):
        # Setup node
        logger.debug("Starting network...")
        self._pyre_node = Pyre(self._name)
        self._name = self._pyre_node.name()
        for header in self._headers:
            self._pyre_node.set_header(*header)
        self._pyre_node.join(self._group)
        self._pyre_node.start()

    def whisper(self, peer, msg_p):
        if self._format == DataFormat.V3:
            return  # no-op
        elif self._format == DataFormat.V4:
            self._pyre_node.whisper(peer, msg_p)
        else:
            raise NotImplementedError()

    def rejoin(self):
        for sensor_uuid, sensor in list(self.sensors.items()):
            self._execute_callbacks(
                {
                    "subject": "detach",
                    "sensor_uuid": sensor_uuid,
                    "sensor_name": sensor["sensor_name"],
                    "host_uuid": sensor["host_uuid"],
                    "host_name": sensor["host_name"],
                }
            )
        self._pyre_node.leave(self._group)
        self._pyre_node.join(self._group)

    def stop(self):
        logger.debug("Stopping network...")
        self._pyre_node.leave(self._group)
        self._pyre_node.stop()
        self._pyre_node = None

    def handle_event(self):
        if not self.has_events:
            return
        event = PyreEvent(self._pyre_node)
        uuid = event.peer_uuid
        if event.type == "SHOUT" or event.type == "WHISPER":
            try:
                payload = event.msg.pop(0).decode()
                msg = serial.loads(payload)
                msg["subject"]
                msg["sensor_uuid"]
                msg["host_uuid"] = event.peer_uuid.hex
                msg["host_name"] = event.peer_name
            except serial.decoder.JSONDecodeError:
                logger.warning(f'Malformatted message: "{payload}"')
            except (ValueError, KeyError):
                logger.warning(f"Malformatted message: {msg}")
            except Exception:
                logger.debug(tb.format_exc())
            else:
                if msg["subject"] == "attach":
                    if self.sensors.get(msg["sensor_uuid"]):
                        # Sensor already attached. Drop event
                        return
                    sensor_type = SensorType.supported_sensor_type_from_str(
                        msg["sensor_type"]
                    )
                    if sensor_type is None:
                        logger.debug(
                            "Unsupported sensor type: {}".format(msg["sensor_type"])
                        )
                        return
                elif msg["subject"] == "detach":
                    sensor_entry = self.sensors.get(msg["sensor_uuid"])
                    # Check if sensor has been detached already
                    if not sensor_entry:
                        return
                    msg.update(sensor_entry)
                else:
                    logger.debug(f"Unknown host message: {msg}")
                    return
                self._execute_callbacks(msg)
        elif event.type == "JOIN":
            # possible values for `group_version`
            # - [<unrelated group>]
            # - [<unrelated group>, <unrelated version>]
            # - ['pupil-mobile']
            # - ['pupil-mobile', <version>]
            group_version = event.group.split("-v")
            group = group_version[0]
            version = group_version[1] if len(group_version) > 1 else "0"

        elif event.type == "EXIT":
            gone_peer = event.peer_uuid.hex
            for host_uuid, sensors in list(self._sensors_by_host.items()):
                if host_uuid != gone_peer:
                    continue
                for sensor_uuid, sensor in list(sensors.items()):
                    self._execute_callbacks(
                        {
                            "subject": "detach",
                            "sensor_uuid": sensor_uuid,
                            "sensor_name": sensor["sensor_name"],
                            "host_uuid": host_uuid,
                            "host_name": sensor["host_name"],
                        }
                    )
        else:
            logger.debug(f"Dropping {event}")

    def sensor(
        self, sensor_uuid: str, callbacks: typing.Iterable[NetworkEventCallback] = ()
    ) -> Sensor:
        try:
            sensor_settings = self.sensors[sensor_uuid].copy()
        except KeyError:
            raise ValueError(f'"{sensor_uuid}" is not an available sensor id.')

        sensor_type_str = sensor_settings.pop("sensor_type", "unknown")
        sensor_type = SensorType.supported_sensor_type_from_str(sensor_type_str)

        if sensor_type is None:
            raise ValueError(f'Sensor of type "{sensor_type_str}" is not supported.')

        return Sensor.create_sensor(
            sensor_type=sensor_type,
            format=self._format,
            context=self._context,
            callbacks=callbacks,
            **sensor_settings,
        )

    # Public

    def __str__(self):
        return f"<{__name__} {self._name} [{self._pyre_node.uuid().hex}]>"

    # Private

    @property
    def _group(self) -> str:
        return group_name_from_format(self._format)

    def _execute_callbacks(self, event):
        for callback in self.callbacks:
            callback(self, event)

    def _on_event(self, caller, event):
        if event["subject"] == "attach":
            subject_less = event.copy()
            del subject_less["subject"]
            host_uuid = event["host_uuid"]
            host_sensor = {event["sensor_uuid"]: subject_less}
            try:
                self._sensors_by_host[host_uuid].update(host_sensor)
            except KeyError:
                self._sensors_by_host[host_uuid] = host_sensor
            logger.debug(f'Attached {host_uuid}.{event["sensor_uuid"]}')
        elif event["subject"] == "detach":
            for host_uuid, sensors in self._sensors_by_host.items():
                try:
                    del sensors[event["sensor_uuid"]]
                    logger.debug(f'Detached {host_uuid}.{event["sensor_uuid"]}')
                except KeyError:
                    pass
            hosts_to_remove = [
                host_uuid
                for host_uuid, sensors in self._sensors_by_host.items()
                if len(sensors) == 0
            ]
            for host_uuid in hosts_to_remove:
                del self._sensors_by_host[host_uuid]


class Network(NetworkInterface):
    def __init__(
        self,
        formats: typing.Set[DataFormat] = None,
        context=None,
        name=None,
        headers=(),
        callbacks=(),
    ):
        formats = formats or {DataFormat.latest()}
        self.context = context or zmq.Context()
        self._callbacks = callbacks
        self._nodes = [
            _NetworkNode(
                format=format,
                context=self.context,
                name=name,
                headers=headers,
                callbacks=self._callbacks,
            )
            for format in formats
        ]
        assert len(self._nodes) > 0

    # Public NetworkInterface API

    @property
    def has_events(self) -> bool:
        return any(node.has_events for node in self._nodes)

    @property
    def running(self) -> bool:
        return any(node.running for node in self._nodes)

    @property
    def sensors(self) -> typing.Mapping[str, NetworkSensor]:
        sensors = collections.ChainMap(*(n.sensors for n in self._nodes))
        return dict(sensors)

    @property
    def callbacks(self) -> typing.Iterable[NetworkEventCallback]:
        return self._callbacks

    @callbacks.setter
    def callbacks(self, value: typing.Iterable[NetworkEventCallback]):
        self._callbacks = value
        for node in self._nodes:
            node.callbacks = value

    def start(self):
        for node in self._nodes:
            node.start()

    def whisper(self, peer, msg_p):
        for node in self._nodes:
            node.whisper(peer=peer, msg_p=msg_p)

    def rejoin(self):
        for node in self._nodes:
            node.rejoin()

    def stop(self):
        for node in self._nodes:
            node.stop()

    def handle_event(self):
        for node in self._nodes:
            node.handle_event()

    def sensor(
        self, sensor_uuid: str, callbacks: typing.Iterable[NetworkEventCallback] = ()
    ) -> Sensor:
        for node in self._nodes:
            if sensor_uuid in node.sensors:
                return node.sensor(sensor_uuid=sensor_uuid, callbacks=callbacks)
        raise ValueError(f'"{sensor_uuid}" is not an available sensor id.')


def group_name_from_format(format: DataFormat) -> str:
    return f"pupil-mobile-{format}"
