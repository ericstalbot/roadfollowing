import requests

apikey = open('apikey.txt').read()

r = requests.post(

    'https://ericstalbot.cartodb.com/api/v1/imports/',
    params={
        'api_key':apikey,
        },
    files={
        'file': (
            'vermont_roads.geojson',
            open('vermont_roads.geojson', 'rb'),
            'text/plain',
            {'Expires': '0'})}
    
    


)

print(r.text)