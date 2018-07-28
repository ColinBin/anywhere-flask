# -*- coding: utf-8 -*-
__author__ = 'Colin'
from urllib import request
import json
import requests

test_longitude=str(116.0)
test_latitude=str(39.0)
def LocationToDescriptionWithBaidu(longitude,latitude):
    http_request = 'http://api.map.baidu.com/geocoder/v2/'
    api_key = 'your api key'
    callback = ''
    http_request=http_request+'?ak='+api_key+'&callback='+callback+'&location='+latitude+','+longitude+'&output=json&pois=1'
    with request.urlopen(http_request) as f:
        data=f.read().decode('utf-8')
        data=json.loads(data)

        status=data['status']
        result=None
        if status==0:
            result=data['result']['formatted_address']
        elif status==1:
            print("LocationToDescription_Server Problem\n")
        elif status==5:
            print("LocationToDescription_AK Problem\n")
        elif status==102:
            print("LocationToDescription_Not in the white list\n")
        elif status>=300:
            print("LocationToDescription_Quota exceeded\n")
        else:
            print("LocationToDescription_Uncommon problem")
        return result

def LocationToDescriptionWithGoogle(longitude,latitude):
    base_url='https://maps.googleapis.com/maps/api/geocode/json'
    params={'latlng':latitude+","+longitude,'key':'your api key'}
    response=requests.get(base_url,params=params)
    result=None
    if response.status_code==200:
        data=json.loads(response.text)
        if data['status']=='OK':
            result=data['results'][0]['formatted_address']
    return result


if __name__=='__main__':
    result=LocationToDescriptionWithGoogle(test_longitude,test_latitude)
    if(len(result)>0):
        print(result)
    else:
        print("LocationToDescription_Error!")

