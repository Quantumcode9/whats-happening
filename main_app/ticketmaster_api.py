import requests
import os

def get_ticketmaster_events(keyword, startDateTime=None, size=10):
    url = os.environ['API_BASE_URL'] + "events.json"
    params = {
        'apikey': os.environ['API_KEY'],
        'size': size,
        'sort': 'date,asc'
    }
    if keyword:
        params['keyword'] = keyword
    if startDateTime:
        params['startDateTime'] = startDateTime + "T00:00:00Z"

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()  
    else:
        return None
    

#Details 
def get_event_details(event_id):
    url = os.environ['API_BASE_URL'] + f"events/{event_id}.json"
    params = {'apikey': os.environ['API_KEY']}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()  
    else:
        return None