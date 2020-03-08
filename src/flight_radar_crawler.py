#!/usr/bin/env python3

import requests
import time
import json
import csv
import os
from datetime import timedelta, datetime

def get_flight() -> dict:
    ignore = ["full_count", "version", "stats"]
    url = "https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds=67.24,-28.43,-461.73,461.73&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&maxage=14400&gliders=1&stats=1"

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
              3, 4, 5,
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

    # Build dict to write in JSON
    for key in data.keys():
        clean_data[key] = {}
        for field, value in zip(fields, data[key]):
            clean_data[key].update({field:value})

    return clean_data

def save_data(data: dict, file_type: str = 'json'):
    
    # Format file name
    file_type = file_type.lower()
    filename = f'ads-b_data-{datetime.today().strftime("%H-%M-%S_%d-%m-%Y")}.{file_type}'
    header = True

    if os.path.isfile(filename):
        header = False

    # Write to selected file
    with open(filename, 'a') as ads_b_data:
        if file_type == 'json':
            json.dump(dataframe, ads_b_data, indent=2, separators=(',', ':'))

        elif file_type == 'csv':
            fieldnames = ["Model-S", "Latitude", "Longitude", 3, 4, 5, "Transponder", "Feeder-Station-Code",
              "Aircraft-Model", "Aircraft-Registration", "Timestamp", "From", "To", "Flight-Code", 14, 15,
              "Airline-Flight-Code", 17, "Airline"]

            writer = csv.DictWriter(ads_b_data, fieldnames=fieldnames)

            if header:
                writer.writeheader()

            for keys in data.keys():
                writer.writerow(data[keys])

if __name__ == "__main__":
    dataframe = {}

    duration = timedelta(minutes=5)
    start_time = datetime.utcnow()

    while (datetime.utcnow() - start_time) <= duration:
        try:
            data = get_flight()
            dataframe.update(parser(data))

            if len(dataframe) >= 1500:
                save_data(dataframe, 'csv')
                dataframe.clear()

        except KeyboardInterrupt:
            save_data(dataframe, 'csv')
            break
    else:
        save_data(dataframe, 'csv')
