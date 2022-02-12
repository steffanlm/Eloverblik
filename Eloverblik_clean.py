# -*- coding: utf-8 -*-
import msvcrt
import time
import calendar
import pyeloverblik as el
from datetime import datetime, date
from datetime import timedelta
import json
import schedule
import os
from influxdb import InfluxDBClient

#ENABLING ALL THE NICE COLORS!
import textcolorcoding as c
os.system("")



#mqtt client information
mqtt_enabled = True
if mqtt_enabled:
    import paho.mqtt.client as mqttClient
    mqtt_broker_address = "MQTT_BROKER_IP"
    mqtt_password = "MQTT_PASSWORD"
    mqtt_user = "MQTT_USER"
    mqtt_port = 1883
    mqtt_keepalive = 15
    mqtt_clientname = "eloverblik"
   
def on_connect(client, userdata, flags, rc):
	client.publish("home/scripts/" + mqtt_clientname +"/status/",payload="Online", qos=0, retain=True)

def on_disconnect(client, userdata, rc=0):
    if mqtt_enabled:
        mqtt_client.loop.stop()
    
client = InfluxDBClient(host='IP FOR INFLUXDB', port=8086, database='INFLUX DATABASENAME')

data_meter_token = [
    ["meterid1","refresh_token1"],
    ["meterid2","refresh_token2"],
    ["meterid3","refresh_token3"],
    ["meterid4","refresh_token4"],
    ["meterid5","refresh_token5"]
    ]

print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Starting script" + c.CEND)

def get_data(meter_id, refresh_token):
    global raw_data
    startTime = time.time()
    
    time_from = datetime.now()-timedelta(days=14)
    time_to = datetime.now()
    print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Trying to fetch data from meter " + meter_id + c.CEND)
    tok = el.Eloverblik(refresh_token)
    
    if tok:
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Got refresh token " + c.CEND)
    else:
        print(c.CRED + "[WARNING] ["+ str(datetime.now())[0:-3] +"] Not able to get refresh token - check your refresh token is active @ eloverblik.dk" + c.CEND)
        
    try:
        raw_data = tok.get_time_series(meter_id, time_from, time_to)
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Got time series - loading json data" + c.CEND)
        json_response = json.loads(raw_data.body)
    except Exception as e:
        print(c.CRED + "[WARNING] ["+ str(datetime.now())[0:-3] +"] Something failed fetching time series..." + c.CEND)
        print(e)
        json_response = ""

    try:
        if json_response["StatusCode"]:
            print(c.CRED + "[WARNING] ["+ str(datetime.now())[0:-3] +"] Data not loaded [" + str(json_response["StatusCode"]) +"] message [" + json_response["Message"] + "]" + c.CEND)
    except:
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] No JSON errors - continuing" + c.CEND)
       
    result = json_response
    metering_data = []
    
    measurement_name = 'kWh'
    
    if 'result' in result and len(result['result']) > 0:
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Parsing data " + c.CEND)
        market_document = result['result'][0]['MyEnergyData_MarketDocument']
        if 'TimeSeries' in market_document and len(market_document['TimeSeries']) > 0:
            time_series = market_document['TimeSeries']
            for t in time_series:
                Period = t['Period']
                for p in Period:
                    periodestart = p['timeInterval']['start']
                    resolution = p['resolution']
                    date_time_obj = datetime.strptime(periodestart, '%Y-%m-%dT%H:%M:%SZ')
                    hour_start = date_time_obj.hour
                    point = p['Point']
                    for i in point:
                        offset = 1
                        
                        if hour_start == 23:
                            offset = 1 
                        elif hour_start == 22:
                            offset = 2 

                        if len(point) == 23: #(vinter- til sommertid)
                            offset = offset

                        elif len(point) == 25: #(sommer- til vintertid)
                            offset = offset  
                        
                        datoTid = date_time_obj + timedelta(hours=int(i['position'])+offset-2)
                        metering_data.append(
                            "{measurement},meterID={meterID} værdi={value},resolution=\"{resolution}\",position=\"{position}\",quality=\"{quality}\" {time}"
                            .format(measurement=measurement_name,
                                    meterID=meter_id,
                                    resolution=resolution,
                                    position=i['position'],
                                    quality=i['out_Quantity.quality'],
                                    value=float(i['out_Quantity.quantity']),
                                    time=calendar.timegm(time.strptime(str(datoTid),'%Y-%m-%d %H:%M:%S')))) #
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] " + str(len(metering_data)) + " lines parsed" + c.CEND)
    else:
        print(c.CRED + "[WARNING] ["+ str(datetime.now())[0:-3] +"] No data to parse" + c.CEND)
    
    if metering_data:
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Writing metering data to InfluxDB" + c.CEND)
        client.write_points(metering_data, protocol='line', time_precision='s')
        succes = True
    else:
        print(c.CRED + "[WARNING] ["+ str(datetime.now())[0:-3] +"] No metering to write to InfluxDB" + c.CEND)
        succes = False
    
    print (c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Script took " + str(time.time() - startTime)[0:6] + " seconds !" + c.CEND)
    
    if succes:
        print (c.CYELLOW2 + "[WAITING] ["+ str(datetime.now())[0:-3] +"] Waiting for 24 hours before fetching new data!" + c.CEND)
        schedule.cancel_job('hourly')
    if not succes:
        print (c.CRED + "[WAITING] ["+ str(datetime.now())[0:-3] +"] Waiting for 1 hour to retry fetching data!" + c.CEND)
        schedule.every().hour.do(get_data).tag('hourly')
    
if __name__ == '__main__':
    if mqtt_enabled:
        mqtt_client = mqttClient.Client(mqtt_clientname)
        mqtt_client.on_connect = on_connect
        mqtt_client.username_pw_set(mqtt_user, password=mqtt_password)    #set username and password
        mqtt_client.will_set("home/scripts/" + mqtt_clientname +"/status/", payload="Offline", qos=0, retain=True)
        mqtt_client.connect(mqtt_broker_address, mqtt_port, mqtt_keepalive)
        mqtt_client.loop_start()
    #CREATING SCHEDULE JOBS FOR SCRIPT TO HANDLE copied from computerStatusInflux!
    schedule.every().day.do(get_data).tag('daily')
    print("[INITIALIZE] ["+ str(datetime.now())[0:-3] +"] In console: Press '"+ c.CRED2 + "q" + c.CEND + "' to quit")
    print("[INITIALIZE] ["+ str(datetime.now())[0:-3] +"] In console: Press '"+ c.CRED2 + "m" + c.CEND + "' to manually fetch data")
    for meter in data_meter_token:
        get_data(meter[0], meter[1])

while True:
    try:
        schedule.run_pending()
    except:
        print(c.CRED + "[WARNING] ["+ str(datetime.now())[0:-3] +"] Not able to run \" pending \"" + c.CEND)
    time.sleep(1)

    if msvcrt.kbhit():
        pressedKey = msvcrt.getch()
        if ord(pressedKey) == 27 or ord(pressedKey) == 113:
            print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] [Q]uit button pressed" + c.CEND)
            if mqtt_enabled:
                mqtt_client.loop.stop()
            break
        if ord(pressedKey) == 109:
            print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] [M]anual fetch button pressed" + c.CEND)
            schedule.cancel_job('hourly')
            for meter in data_meter_token:
                get_data(meter[0], meter[1])
