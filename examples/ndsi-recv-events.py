import time

# https://github.com/pupil-labs/pyndsi/tree/v1.0
import ndsi  # Main requirement

EVENT_TYPE = "event"  # Type of sensors that we are interested in
SENSORS = {}  # Will store connected sensors


def main():
    # Start auto-discovery of Pupil Invisible Companion devices
    network = ndsi.Network(formats={ndsi.DataFormat.V4}, callbacks=(on_network_event,))
    network.start()

    try:
        # Event loop, runs until interrupted
        while network.running:
            # Check for recently connected/disconnected devices
            if network.has_events:
                network.handle_event()

            # Iterate over all connected devices
            for event_sensor in SENSORS.values():
                # Fetch recent sensor configuration changes,
                # required for pyndsi internals
                while event_sensor.has_notifications:
                    event_sensor.handle_notification()

                # Fetch recent event data
                for event in event_sensor.fetch_data():
                    # Output: EventValue(timestamp, label)
                    print(event_sensor, event)

            time.sleep(0.1)

    # Catch interruption and disconnect gracefully
    except (KeyboardInterrupt, SystemExit):
        network.stop()


def on_network_event(network, event):
    # Handle event sensor attachment
    if event["subject"] == "attach" and event["sensor_type"] == EVENT_TYPE:
        # Create new sensor, start data streaming,
        # and request current configuration
        sensor = network.sensor(event["sensor_uuid"])
        sensor.set_control_value("streaming", True)
        sensor.refresh_controls()

        # Save sensor s.t. we can fetch data from it in main()
        SENSORS[event["sensor_uuid"]] = sensor
        print(f"Added sensor {sensor}...")

    # Handle event sensor detachment
    if event["subject"] == "detach" and event["sensor_uuid"] in SENSORS:
        # Known sensor has disconnected, remove from list
        SENSORS[event["sensor_uuid"]].unlink()
        del SENSORS[event["sensor_uuid"]]
        print(f"Removed sensor {event['sensor_uuid']}...")


main()  # Execute example
