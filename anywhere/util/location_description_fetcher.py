# -*- coding: utf-8 -*-
__author__ = 'Colin'
import json

import requests
from config import GOOGLE_API_HOST_NAME, GOOGLE_API_KEY

test_longitude = str(116.0)
test_latitude = str(39.0)


def location_to_description(longitude, latitude):
    params = {'latlng': latitude + "," + longitude, 'key': GOOGLE_API_KEY}
    response = requests.get(GOOGLE_API_HOST_NAME, params=params)
    if response.status_code == 200:
        return json.loads(response.text)
    return None


if __name__ == '__main__':
    print(location_to_description(test_longitude, test_latitude))
