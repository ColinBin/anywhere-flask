# -*- coding: utf-8 -*-
__author__ = 'Colin'
import json

import requests

test_longitude = str(116.0)
test_latitude = str(39.0)


def location_to_description(longitude, latitude):
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'latlng': latitude + "," + longitude, 'key': 'AIzaSyDJdDkeyLQznOrFotIGzZk3WwMUiik2W_U'}
    response = requests.get(base_url, params=params)
    result = None
    print(response.text)
    if response.status_code == 200:
        data = json.loads(response.text)
        if data['status'] == 'OK':
            result = data['results'][0]['formatted_address']
    return result


if __name__ == '__main__':
    result = location_to_description(test_longitude, test_latitude)
    if len(result) > 0:
        print(result)
    else:
        print("location_to_description error!")
