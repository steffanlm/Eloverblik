### Eloverblik to InfluxDB with Python
Small python script to fetch meter data from eloverblik.dk.
The script fetches all the Eloverblik data once every 24 hour, if it fails, it tries again the next day, and issues a local warning in the CLI.
Script is created for Windows, but feel free to alter it to use on other OS.
Script is now able to send information about script status ("Online" and "Offline"), to remotely show if the script is in full function. Uses basic MQTT functionality with last-wish.

### Prerequisite
You need to ensure, you have the following prerequisites installed (thats my current versions, so I haven't tested with other versions, but feel free to post if script is running well with other versions)
```
pyeloverblik==0.0.7
influxdb==5.3.0
schedule==0.6.0
paho-mqtt==1.5.0
```
Paho-mqtt is only needed if MQTT is enabled in the script.

### How to start
Update the following lines in the Eloverblik_clean.py file: 

Change "IP FOR INFLUXDB" to the host IP for your InfluxDB and change the "INFLUX DATABASENAME to the databasename you wish to use
```
client = InfluxDBClient(host='IP FOR INFLUXDB', port=8086, database='INFLUX DATABASENAME')
```
Enable or disable MQTT support:
```
    mqtt_enabled = True
```
If MQTT is enabled, make sure to set login informtion for your MQTT broker
```
    mqtt_broker_address = "MQTT_BROKER_IP"
    mqtt_password = "MQTT_PASSWORD"
    mqtt_user = "MQTT_USER"
```    
Get your TOKEN and Meter ID from Eloverblik.dk and enter in the following array
```
data_meter_token = [
    ["meterid1","refresh_token1"],
    ["meterid2","refresh_token2"],
    ["meterid3","refresh_token3"],
    ["meterid4","refresh_token4"],
    ["meterid5","refresh_token5"]
    ]
```
### Run the UI
The script can be started directly as a batch file in Windows

Create a *.bat file, to run the file directly - I'm using a batch file with this content, to switch to the script location, before executing the script with a simple shell command.
The script is running in a CLI, and show different states.
```
ECHO ON
call C:\Users\Steffan\anaconda3\Scripts\activate.bat C:\Users\Steffan\anaconda3
REM A batch script to execute a Python script
SET PATH=%PATH%;C:\Users\Steffan\anaconda3\pythonw.exe
z:
cd python
cd Elforbrug
python Eloverblik.py
PAUSE
```
