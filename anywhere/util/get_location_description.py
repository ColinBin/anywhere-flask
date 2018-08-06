# -*- coding: utf-8 -*-
__author__ = 'Colin'
import json

import requests

test_longitude = str(116.0)
test_latitude = str(39.0)


def location_to_description(longitude, latitude):
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'latlng': latitude + "," + longitude, 'key': 'AIzaSyDYxbjM75Px7fdZzThCBVwghytGtmdD7wI'}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return json.loads(response.text)
    return None


if __name__ == '__main__':
    print(location_to_description(test_longitude, test_latitude))
