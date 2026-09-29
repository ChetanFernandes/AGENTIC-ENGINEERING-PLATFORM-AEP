import requests
AUTH_SERVER_URL = "http://127.0.0.1:8000"

def register_client():
    registration_url = f"{AUTH_SERVER_URL}/register"
    client_metadata = {
        "client_name" : "AEP",
        "redirect_uris" : ["http://127.0.0.1:9000/callback"],
        "grant_types" : ["authorization_code", "refresh_token"],
         "response_types": ["code"]} # This tells the OAuth server: When I request authorization, I expect the authorization server to return a code."
    response = requests.post(registration_url,json = client_metadata)
    response.raise_for_status()
    return response.json() # The FastMCP OAuth server processes this request and creates/registers a client.

#requests.post() → send the request,  # requests.post() sends data to a server using HTTP POST
#raise_for_status() → check whether it worked
#response.json() → read the response
#200 → Success
#201 → Created / Success
#400 → Bad request
#401 → Unauthorized
#403 → Forbidden
#404 → Not found
#500 → Server error

'''
grant_types
├── authorization_code → get access token using authorization code
└── refresh_token      → get a new access token later

response_types
└── code               → authorization endpoint returns an authorization code
'''


