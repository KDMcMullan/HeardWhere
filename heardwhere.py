import json
import paho.mqtt.client as mqtt
import maidenhead
from geopy.geocoders import Nominatim

# Configuration
MQTT_BROKER = "mqtt.pskreporter.info"
MQTT_PORT = 1883
TOPIC = "pskreporter/log"
TARGET_CALLSIGN = "YOUR_TARGET_CALLSIGN"  # Replace with the callsign you want to track
geolocator = Nominatim(user_agent="maidenhead_locator_to_region")

# Store regions where the callsign is heard
regions_heard = set()

# Convert Maidenhead locator to region
def get_region_from_locator(locator):
    try:
        lat, lon = maidenhead.to_location(locator)
        location = geolocator.reverse((lat, lon), language="en")
        if location and location.address:
            return location.raw.get("address", {}).get("country", "Unknown Region")
    except Exception as e:
        print(f"Error resolving locator {locator}: {e}")
    return "Unknown Region"

# Process incoming MQTT messages
def on_message(client, userdata, message):
    global regions_heard
    try:
        payload = json.loads(message.payload.decode())
        reporter_callsign = payload.get("reporter", {}).get("callsign", "")
        target_callsign = payload.get("target", {}).get("callsign", "")
        target_locator = payload.get("target", {}).get("grid", "")

        # If the message is about the target callsign
        if target_callsign == TARGET_CALLSIGN and target_locator:
            region = get_region_from_locator(target_locator)
            if region and region not in regions_heard:
                regions_heard.add(region)
                print(f"{TARGET_CALLSIGN} is heard in: {region}")

    except Exception as e:
        print(f"Error processing message: {e}")

# Connect to MQTT broker
def main():
    client = mqtt.Client()
    client.on_message = on_message

    print(f"Connecting to {MQTT_BROKER}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(TOPIC)

    print(f"Listening for reports about {TARGET_CALLSIGN}...")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        client.disconnect()

if __name__ == "__main__":
    main()
