import json
import os
import time
import random 
import datetime
from paho.mqtt import client as mqtt_client 

#TCP Connection
broker = 'mosquitto' #οριστηκε στο docker-compose
port = 1883 #standard mqtt port 
topic = "publishers/data" #προσωρινος φακελος που στελνονται οι μετρησεις απο sensors
device_name = os.environ.get('DEVICE_NAME') #διαβαζει ονομα sensor απο το docker-compose ('DEVICE_NAME')
client_id = f'python-mqtt-{device_name}' # ονομα συνδεσης broker , mqtt id 

def connect_mqtt(): #χρησιμοποιηθηκε paho-mqtt version 2 για υποστηριξη νεοτερων εκδοσεων mqtt
    # For paho-mqtt 2.0.0, you need to add the properties parameter.
    def on_connect(client, userdata, flags, rc, properties=None): #επιπλεον πληροφοριες απο broker , αν δεν στειλει θεωρησε none
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID    
    # For paho-mqtt 2.0.0, you need to set callback_api_version.
    client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


#Tα μηνύματα αυτών θα είναι πχ ,
# {
#   "device_name": "sensor_01",
#   "timestamp": "2026-02-01T08:30:00Z",
#   "value": 2
# }

def publish(client): #συνάρτηση που στέλνει μηνύματα στο MQTT broker
    while True:
        time.sleep(1) #καθυστέρηση 1 δευτερολέπτου μεταξύ των αποστολών μηνυμάτων

        value = random.randint(0, 100)  # τυχαία τιμή για το πεδίο value

        payload = { #δημιουργία του payload με τις απαιτούμενες πληροφορίες
            "device_name": device_name, #όνομα της συσκευής που στέλνει το μήνυμα
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),#χρονική στιγμή αποστολής του μηνύματος σε μορφή ISO 8601 με UTC timezone (προσθήκη "Z" για να υποδηλώσει UTC)
            "value": value 
        }
        #μετατροπή του payload σε JSON string για αποστολή μέσω MQTT
        msg = json.dumps(payload) 
        result = client.publish(topic, msg) #αποστολή του μηνύματος στο topic και αποθήκευση του αποτελέσματος της αποστολής
        # result: [0, 1]
        status = result[0] #έλεγχος αν το μήνυμα στάλθηκε επιτυχώς (0) ή όχι (1)
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`") #επιβεβαίωση αποστολής μηνύματος
        else:
            print(f"Failed to send message to topic {topic}") #επιβεβαίωση αποτυχίας αποστολής μηνύματος


def run():
    client = connect_mqtt() #συνδεση με mqtt broker , αποθηκευση συνδεσης στη μεταβλητη 'client' 
    client.loop_start() #εκκίνηση του loop για να διατηρείται η σύνδεση ενεργή
    publish(client) #κλήση της συνάρτησης publish για αποστολή μηνυμάτων

if __name__ == '__main__':
    run() #εκτελεση της run 
