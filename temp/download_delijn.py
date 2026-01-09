########### Python 3.2 #############
import requests

url = "https://api.delijn.be/gtfs/static/v3/gtfs_transit.zip"

hdr ={
# Request headers
'Cache-Control': 'no-cache',
'Ocp-Apim-Subscription-Key': '5bfeb829eda743eab440c44567c22f65',
}

r = requests.get(url, headers=hdr)

with open('./delijn', 'wb') as f:
    f.write(r.content)


