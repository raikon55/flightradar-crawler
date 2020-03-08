#!/usr/bin/env python3

import os
import sys
import csv
import json
import time
import requests
import MySQLdb as mariadb
from datetime import timedelta, datetime

def get_flight() -> dict:
    ignore = ["full_count", "version", "stats"]
    
    # Focus on Europe
    url = "https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds=46.82,41.38,-6.96,23.49&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&maxage=14400&gliders=1&stats=1" 
    
    # All globe
    #url = "https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds=67.24,-28.43,-461.73,461.73&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&maxage=14400&gliders=1&stats=1"

    # Request with fake header, otherwise you will get an 403 HTTP error
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})

    # Parse the JSON
    data = r.json()
    for x in ignore:
        data.pop(x)

    return data

def parser(data: dict) -> dict:
    clean_data = {}

    # Parameters returned of request
    fields = ["Model-S",
              "Latitude",
              "Longitude",
              "Fly-Direction",
              "Altitude",
              "Ground-Speed",
              "Transponder",
              "Feeder-Station-Code",
              "Aircraft-Model",
              "Aircraft-Registration",
              "Timestamp",
              "From",
              "To",
              "Flight-Code",
              14, 15,
              "Airline-Flight-Code",
              17,
              "Airline"]

    # Build the dict to save after
    for key in data.keys():
        clean_data[key] = {}
        for field, value in zip(fields, data[key]):
            clean_data[key].update({field:value})

    return clean_data

def save_data(data: dict, file_type: str = 'json'):

    # If want save on a database
    if file_type == 'db':
        connection_database(data)

    else:
        # Format file name
        file_type = file_type.lower()
        filename = f'ads-b_data-{datetime.today().strftime("%H-%M-%S_%d-%m-%Y")}.{file_type}'
        header = True

        if os.path.isfile(filename):
            header = False

        # If is a file, write to selected file
        with open(filename, 'a') as ads_b_data:
            if file_type == 'json':
                json.dump(dataframe, ads_b_data, indent=2, separators=(',', ':'))

            elif file_type == 'csv':
                fieldnames = ["Model-S", "Latitude", "Longitude", "Fly-Direction",
                "Altitude", "Ground-Speed", "Transponder", "Feeder-Station-Code",
                "Aircraft-Model", "Aircraft-Registration", "Timestamp", "From", "To",
                "Flight-Code", 14, 15, "Airline-Flight-Code", 17, "Airline"]

                writer = csv.DictWriter(ads_b_data, fieldnames=fieldnames)

                if header:
                    writer.writeheader()

                for keys in data.keys():
                    writer.writerow(data[keys])

def connection_database(data:dict):
    query:str = "INSERT INTO flightradar(`model_s`,`latitude`,`longitude`,`fly_direction`,`altitude`,`ground_speed`,`transponder`,`feeder_station`,`aircraft_model`,`aircraft_registration`,`timestamp`,`origin`,`destination`,`flight_code`,`column14`,`column15`,`airline_flight_code`,`column17`,`airline`)\
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    insert_items = []

    # Transform data into a list of tuples
    for nested_dict in data.values():
        insert_items.append(tuple(nested_dict.values()))

    connection = mariadb.connect(host=sys.argv[2], user=sys.argv[3], passwd=sys.argv[4], db=sys.argv[5])
    cursor = connection.cursor()

    try:
        cursor.executemany(query, insert_items)
    except (mariadb._exceptions.OperationalError, mariadb._exceptions.DataError) as exc:
        print(exc)
        pass
    except exc:
        print(exc)
        connection.rollback()
        return

    connection.commit()
    connection.close()

if __name__ == "__main__":
    dataframe = {}

    duration = timedelta(minutes=int(sys.argv[1]))
    start_time = datetime.utcnow()

    while (datetime.utcnow() - start_time) <= duration:
        try:
            data = get_flight()
            dataframe.update(parser(data))
            save_data(dataframe, 'db')
            dataframe.clear()

        except KeyboardInterrupt:
            save_data(dataframe, 'db')
            break
    else:
        save_data(dataframe, 'db')
