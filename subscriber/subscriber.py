# python 3.11
import os 
import random
import json
import psycopg2
import time
from paho.mqtt import client as mqtt_client


broker = 'mosquitto'
port = 1883
topic = "publishers/data"
# Generate a Client ID with the subscribe prefix. Μοναδικο ID στον broker , avoid conflicts 
client_id = f'subscriber-{random.randint(0, 100)}' 
# username = 'emqx'
# password = 'public'

#στοιχεια database απο το docker-compose 
DB_NAME = os.environ.get("DB_NAME", "foo")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")
DB_HOST = os.environ.get("DB_HOST", "db")

# Ομαδοποίηση στοιχείων σύνδεσης σε dictionary
DB_PARAMS = {
    "database": DB_NAME,
    "user": DB_USER,
    "password": DB_PASS,
    "host": DB_HOST
}

def connect_db():
    #συναρτηση για συνδεση στην timescaleDB 
    while True:
        try: #δοκιμη συνδεσης με τα στοιχεια που ορισαμε
            conn = psycopg2.connect(**DB_PARAMS)
            print("Connected to TimescaleDB (Database: foo)!")
            return conn #αν πετυχει επιστρεφει την συνδεση 
        except Exception as e:
            print(f"Database connection failed, retrying in 2s... ({e})")
            time.sleep(2)

def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc, properties=None):
        #rc = return code
        if rc == 0: #επιτυχης συνδεση
            print("Connected to MQTT Broker!")
        else: #σφαλμα συνδεσης
            # rc = 1: Λάθος έκδοση πρωτοκόλλου
            # rc = 2: Λάθος Client ID
            # rc = 3: Ο Broker δεν είναι διαθέσιμος
            # rc = 4/5: Πρόβλημα με Username/Password
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)#ονομα στον subscriber

    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    #συνδεση στον broker , mosquitto & port 1883
 # Δοκιμάζει να συνδεθεί μέχρι να το πετύχει
    while True:
        try:
            client.connect(broker, port)
            break
        except ConnectionRefusedError:
            print("MQTT Broker not ready yet, retrying in 2 seconds...")
            time.sleep(2)
            
    return client

#συναρτηση που αποφασιζει τι θα γινει καθε φορα που ενας αισθητηρας στελνει δεδομενα
def subscribe(client: mqtt_client, db_conn):
    def on_message(client, userdata, msg):
        try:
            #μετατροπη σε dictionary 
            data = json.loads(msg.payload.decode()) #decode : bytes -> text , json.loads : text -> dictionary
            print(f"Λήψη: {data}")

            #create cursor
            cur = db_conn.cursor()

            #sql insert
            #ονοματα στηλων : timestamp, device_name, value
            query = "INSERT INTO sensors_data (timestamp, device_name, value) VALUES (%s, %s, %s)"
            #timestamp απο JSON
            cur.execute(query, (data['timestamp'], data['device_name'], data['value']))

            #commit - σωζει αλλαγες
            db_conn.commit()
            cur.close()
            
        except Exception as e:
            print(f"Σφάλμα κατά την αποθήκευση στη βάση: {e}")
            db_conn.rollback() #ακυρωση αν σφαλμσ

    #activate subscriber 
    client.subscribe(topic)
    client.on_message = on_message

def run():
    #συνδεση στην βαση 
    db_conn = connect_db()
    #συνδεση στο mqtt
    client = connect_mqtt()
    #ληψη μηνυματων
    subscribe(client, db_conn)
    client.loop_forever()


if __name__ == '__main__':
    run()
