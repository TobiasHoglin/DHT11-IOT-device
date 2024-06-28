# main.py -- put your code here!
import dht
import time                   # Allows use of time.sleep() for delays
from mqtt import MQTTClient   # For use of MQTT protocol to talk to Adafruit IO
import machine                # Interfaces with hardware components
from machine import Pin       # Define pin
import keys                   # Contain all keys used here
import wifiConnection         # Contains functions to connect/disconnect from WiFi 

# BEGIN SETTINGS
# These need to be change to suit your environment
DATA_INTERVAL = 40000       # milliseconds, every 40 sec
last_data_sent_ticks = 0    # milliseconds
led = Pin("LED", Pin.OUT)   # On-board LED pin initialization for Raspberry Pi Pico W
#led = Pin(15, Pin.OUT)     # external led
tempSensor = dht.DHT11(machine.Pin(27)) 

def send_data():
    global last_data_sent_ticks
    global DATA_INTERVAL

    if ((time.ticks_ms() - last_data_sent_ticks) < DATA_INTERVAL):
        return; # Too soon since last one sent.

    try:
        tempSensor.measure()
        temperature = tempSensor.temperature()
        humidity = tempSensor.humidity()

        # Debugging: Print raw sensor data
        print("Measured temperature: {}C".format(temperature))
        print("Measured humidity: {}%".format(humidity))

        # Publishing temperature
        print("Publishing temperature: {} to {} ... ".format(temperature, keys.AIO_TEMP_FEED), end='')
        client.publish(topic=keys.AIO_TEMP_FEED, msg=str(temperature))
        print("DONE")

        # Publishing humidity
        print("Publishing humidity: {} to {} ... ".format(humidity, keys.AIO_HUM_FEED), end='')
        client.publish(topic=keys.AIO_HUM_FEED, msg=str(humidity))
        print("DONE")

        
    except Exception as e:
        print("FAILED")
    finally:
        last_data_sent_ticks = time.ticks_ms()

# Callback Function to respond to messages from Adafruit IO
def sub_cb(topic, msg):                       # sub_cb means "callback subroutine"
    print("Received message:", (topic, msg))  # Outputs the message that was received. Debugging use.
    print("Message type:", type(msg))
    print("Message content:", msg)
    if msg == b"ON":             # If message says "ON" ...
        led.on()                 # ... then LED on
        print("Tobias ON") 
    elif msg == b"OFF":          # If message says "OFF" ...
        led.off()                # ... then LED off
        print("Tobias OFF") 
    else:                        # If any other message is received ...
        print("Unknown message") # ... do nothing but output that it happened.

print('pymaker wifi + mqtt 1.00 onboard led') #debugprints
# Try WiFi Connection
try:
    ip = wifiConnection.connect()
except KeyboardInterrupt:
    print("Keyboard interrupt")
    machine.reset()

# Use the MQTT protocol to connect to Adafruit IO
client = MQTTClient(keys.AIO_CLIENT_ID, keys.AIO_SERVER, keys.AIO_PORT, keys.AIO_USER, keys.AIO_KEY)

# Subscribed messages will be delivered to this callback
client.set_callback(sub_cb)
print("Callback set.")
client.connect()
print("MQTT client connected.")
client.subscribe(keys.AIO_LIGHTS_FEED)
print("Subscribed to topic: %s" % keys.AIO_LIGHTS_FEED)

try:                      # Code between try: and finally: may cause an error
                          # so ensure the client disconnects the server if
                          # that happens.
    while True:              # Repeat this loop forever
        client.check_msg()   # Action a message if one is received. Non-blocking.
        send_data()          # Send temperature to Adafruit IO if it's time.
        time.sleep(1)        # Add a small delay to avoid too tight looping
finally:                  # If an exception is thrown ...
    client.disconnect()   # ... disconnect the client and clean up.
    client = None
    wifiConnection.disconnect()
    print("Disconnected from Adafruit IO.")
