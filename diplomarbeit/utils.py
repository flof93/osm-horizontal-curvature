import requests

def get_bounding_box(query):
    # Nominatim-Url
    url = "https://nominatim.openstreetmap.org/search"
    headers = {'User-agent': 'Mozilla/5.0'}

    # Parameter
    parameters = {
        'q' : query,
        'format' : 'json',
        'addressdetails' : 1
    }

    # Anfrage an Nominatim
    response = requests.get(url, params = parameters, headers=headers)

    # Wenn Anfrage erfolgreich war. (Status 200)
    if response.status_code == 200:
        results = response.json()

        if results:
            result = results[0]
            bbox = result.get('boundingbox')

            if bbox:
                return [float(coord) for coord in bbox]
            else:
                return []

        else:
            return []
    else:
        raise requests.exceptions.HTTPError
