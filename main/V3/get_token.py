import requests

CLIENT_ID = "21d80d19190544d0bbe39c06c8af635d"
CLIENT_SECRET = "tEHJW0IkA76jRj680UVZ4hfqwaAB5JPp"

def get_access_token():
    url = "https://oauth.battle.net/token"
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    response.raise_for_status()
    token_data = response.json()
    return token_data["access_token"]

ACCESS_TOKEN = get_access_token()
print(ACCESS_TOKEN)
