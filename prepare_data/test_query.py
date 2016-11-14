import requests
from os.path import join, dirname

apikey = open(join(dirname(dirname(__file__)),'apikey.txt')).read()

r = requests.post(

    'https://ericstalbot.cartodb.com/api/v2/sql',
    params={
        'api_key': apikey,
        'q':'SELECT * FROM vermont_roads limit 4',
        'format':'GeoJSON'
        },
)

print(r.text)