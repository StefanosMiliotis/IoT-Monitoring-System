# IoT Monitoring System 

## MQTT-based Sensor Monitoring System with TimescaleDB

## Architecture 
Collection of sensor measurements with MQTT, storage in TimescaleDB, and retrieval through FastAPI.

Publishers (1-3) (sensors) → Mosquitto broker (mqtt message handling) → Subscriber (receiver, receives and records messages in database) → Database

![Screenshot](pipeline.png)

* **MQTT Broker:** Using [Eclipse Mosquitto](https://hub.docker.com/_/eclipse-mosquitto) via Docker for message handling.
* **MQTT Clients (Publishers/Subscriber):** Developed in Python 3.11 with `paho-mqtt` library,, [EMQX Guide](https://www.emqx.com/en/blog/how-to-use-mqtt-in-python).
* **Database:** [TimescaleDB](https://www.tigerdata.com/docs/self-hosted/latest/install/installation-docker) 

## Current Stage

**26/02/2026**
* **Completed `docker-compose.yml`**

**27/02/2026 MQTT Publisher**
* implemented `publisher.py` with paho-mqtt library 2.0 version [EMQX Guide](https://www.emqx.com/en/blog/how-to-use-mqtt-in-python)
* json payload (device_name, timestamp{ISO 8601 UTC})

**28/02/2026 Completion of publisher.py**

**01/03/2026 Dockerfile for publisher & subscriber**

**03/03/2026 Backend Completion**
* **-update mosquitto.conf**
* **-update publishers.py**
* **-add & complete subscribers.py**
* **-database setup: creation of sensors_data table and conversion to hypertable** [TimescaleDB](https://www.tigerdata.com/docs/self-hosted/latest/install/installation-docker)
* **-fixed bugs :**
    * **Connection Refused (Mosquitto)**
        broker was rejecting connections, solved via mosquitto.conf
    * **Container Race Condition**
        python scripts were starting before mosquitto broker loaded, solved with try...except + time.sleep(2)
    * **Paho-MQTT v2 Compatibility**
        problem with on_connect parameters, solved with CallbackAPIVersion.VERSION2 and properties=None of the subscriber
    * **SQL Insert Data Mismatch**
        sql query in the subscriber was using NOW() from database instead of timestamp from sensor JSON