### Eloverblik to InfluxDB with Python
Small python script to fetch meter data from eloverblik.dk.
The script fetches all the Eloverblik data once every 24 hour, if it fails, it tries again the next day, and issues a local warning in the CLI

### Prerequisite
You need to ensure, you have the following prerequisites installed (thats my current versions, so I haven't tested with other versions, but feel free to post if script is running well with other versions)
```
pyeloverblik==0.0.7
influxdb==5.3.0
```

### How to start
Update the 3 lines in the Eloverblik_clean.py file: 
Change "IP FOR INFLUXDB" to the host IP for your InfluxDB and change the "INFLUX DATABASENAME to the databasename you wish to use
```
client = InfluxDBClient(host='IP FOR INFLUXDB', port=8086, database='INFLUX DATABASENAME')
```
Get your TOKEN from Eloverblik.dk
```
refresh_token= "TOKEN"
```
Get you METERID from Eloverblik.dk
```
meter = "METERID"
```
### Run the UI
The script can be 

Create a *.bat file, to run the file directly - I'm using a batch file with this content, to switch to the script location, before executing the script with a simple shell command.
The script is running in a CLI, and show different states.

ECHO ON
call C:\Users\Steffan\anaconda3\Scripts\activate.bat C:\Users\Steffan\anaconda3
REM A batch script to execute a Python script
SET PATH=%PATH%;C:\Users\Steffan\anaconda3\pythonw.exe
z:
cd python
cd Elforbrug
python Eloverblik.py
PAUSE
