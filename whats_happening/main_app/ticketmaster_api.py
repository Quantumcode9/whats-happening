import requests

def get_ticketmaster_events(api_key, keyword, startDateTime, size=10):
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        'apikey': api_key,
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
def get_event_details(api_key, event_id):
    url = f"https://app.ticketmaster.com/discovery/v2/events/{event_id}.json"
    params = {'apikey': api_key}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()  
    else:
        return None