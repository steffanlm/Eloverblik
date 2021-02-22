# -*- coding: utf-8 -*-
import msvcrt
import time
import calendar
import pyeloverblik as el
from datetime import datetime
from datetime import timedelta
import json
import schedule
import os
from influxdb import InfluxDBClient

#ENABLING ALL THE NICE COLORS!
import textcolorcoding as c
os.system("")

client = InfluxDBClient(host='IP FOR INFLUXDB', port=8086, database='INFLUX DATABASENAME')

refresh_token= "TOKEN"
meter = "METERID"

print("c.CGREEN + [INFO] ["+ str(datetime.now())[0:-3] +"] Starting script" + c.CEND)

def get_data():
    global raw_data
    startTime = time.time()
    
    time_from = datetime.now()-timedelta(days=7) #days=6
    time_to = datetime.now()
    
    tok = el.Eloverblik(refresh_token)
    
    if tok:
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Got refresh token" + c.CEND)
    else:
        print(c.CRED + "[WARNING] ["+ str(datetime.now())[0:-3] +"] Not able to get refresh token" + c.CEND)
        

    try:
        raw_data  = tok.get_time_series(meter, time_from, time_to)
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Got time series - loading json data" + c.CEND)
        json_response = json.loads(raw_data.body)
        data = raw_data.body
    except:
        print(c.CRED + "[WARNING] ["+ str(datetime.now())[0:-3] +"] Something failed fetching time series..." + c.CEND)
        json_response = ""

    try:
        if json_response["StatusCode"]:
            print(c.CRED + "[WARNING] ["+ str(datetime.now())[0:-3] +"] Data not loaded [" + str(json_response["StatusCode"]) +"] message [" + json_response["Message"] + "]" + c.CEND)
    except:
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] No JSON errors - continueing" + c.CEND)
        
       
    result = json_response
    metering_data = []
    
    measurement_name = 'kWh'
    
    if 'result' in result and len(result['result']) > 0:
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Parsing data " + c.CEND)
        market_document = result['result'][0]['MyEnergyData_MarketDocument']
        if 'TimeSeries' in market_document and len(market_document['TimeSeries']) > 0:
            time_series = market_document['TimeSeries']#[0]
            for t in time_series:
                Period = t['Period']
                for p in Period:
                    periodestart = p['timeInterval']['start']
                    resolution = p['resolution']
                    date_time_obj = datetime.strptime(periodestart, '%Y-%m-%dT%H:%M:%SZ')
                    hour_start = date_time_obj.hour
                    point = p['Point'] #time_series['Period'][0]
    
                    for i in point:
                        if hour_start == 23:
                            offset = 0 #0 normalt
                        elif hour_start == 22:
                            offset = 1 #1 normalt
                        if len(point) == 23: #(vinter- til sommertid)
                            offset = offset + 1
                            if 2 <= int(i['position']) <= 3:
                                offset = offset -2
                        elif len(point) == 25: #(sommer- til vintertid)
                            offset = offset - 1
                            if 2 <= int(i['position']) <= 3:
                                offset = offset +1
    
                        datoTid = date_time_obj + timedelta(hours=int(i['position'])+offset)
                        metering_data.append(
                            "{measurement},meterID={meterID} værdi={value},resolution=\"{resolution}\",position=\"{position}\",quality=\"{quality}\" {time}"
                            .format(measurement=measurement_name,
                                    meterID=meter,
                                    resolution=resolution,
                                    position=i['position'],
                                    quality=i['out_Quantity.quality'],
                                    value=float(i['out_Quantity.quantity']),
                                    time=calendar.timegm(time.strptime(str(datoTid),'%Y-%m-%d %H:%M:%S')))) #
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] " + str(len(metering_data)) + " lines parsed" + c.CEND)
    else:
        print(c.CRED + "[WARNING] ["+ str(datetime.now())[0:-3] +"] No data to parse" + c.CEND)
    
    if metering_data:
        # print(metering_data)
        print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Writing metering data to InfluxDB" + c.CEND)
        client.write_points(metering_data, protocol='line', time_precision='s')
    else:
        print(c.CRED + "[WARNING] ["+ str(datetime.now())[0:-3] +"] No metering to write to InfluxDB" + c.CEND)
    
    print (c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] Script took " + str(time.time() - startTime)[0:6] + " seconds !" + c.CEND)
    
    print (c.CYELLOW2 + "[WAITING] ["+ str(datetime.now())[0:-3] +"] Waiting for 24 hours before fetching new data!" + c.CEND)
    
if __name__ == '__main__':
    #CREATING SCHEDULE JOBS FOR SCRIPT TO HANDLE copied from computerStatusInflux!
    schedule.every(24).hours.do(get_data)
    get_data()

# try:
while True:
    schedule.run_pending()
    time.sleep(1)

    if msvcrt.kbhit():
        pressedKey = msvcrt.getch()
        # print(ord(pressedKey))
        if ord(pressedKey) == 27 or ord(pressedKey) == 113:
            print(c.CGREEN + "[INFO] ["+ str(datetime.now())[0:-3] +"] [Q]uit button pressed" + c.CEND)
            break

# except KeyboardInterrupt:
#     print ("[INFO] ["+ str(datetime.now())[0:-3] +"] Exiting gracefully")
#     schedule.clear
#     schedule.cancel_job(get_data)
