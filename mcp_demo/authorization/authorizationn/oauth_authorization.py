from urllib.parse import urlencode
import hashlib
import base64
import secrets
from mcp_demo.authorization.registration.aep_oauth_client_registration import register_client
import requests

AUTH_SERVER_URL =  "http://127.0.0.1:8000"

def create_oauth_session():
    client_info = register_client()
    print("client_info_sent_by FAST_MCP_after_registration",client_info)

    client_id = client_info["client_id"]
    client_secret = client_info["client_secret"]

    return client_id,client_secret


def build_authorization_url(client_id):
    """Prepare everything AEP will need to ask the OAuth server for authorization."""
    authorization_url = f"{AUTH_SERVER_URL}/authorize" # This is the endpoint where AEP asks the OAuth server to authorize the client

    code_verifier = secrets.token_urlsafe(32) # Create a random secret that AEP will keep
    finger_point = hashlib.sha256(code_verifier.encode()).digest() # Take our secret and mathematically transform it into a fixed fingerprint.
    format = base64.urlsafe_b64encode(finger_point) # Convert that fingerprint into a format that is safe to put inside a URL.
    format_1 = format.rstrip(b"=") # removes trailing = characters from the Base64 representation, as required by the PKCE encoding format.
    code_challenge = format_1.decode() # converts the result from bytes into a normal Python string.

    params = {
                "client_id" : client_id,
                "redirect_uri": "http://127.0.0.1:9000/callback",
                "response_type": "code",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
             }
    
    return {    
            "authorization_url": f"{authorization_url}?{urlencode(params)}", 
            "code_verifier": code_verifier,
           }

   # ? - “The path is finished; everything after this is query parameters.”
   # urlencode(params) - convert that dictionary into the URL query-string format:


def preparing_authorization_request(client_id,client_secret):

    auth_data = build_authorization_url(client_id)

    oauth_session = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code_verifier": auth_data["code_verifier"],
    }

    return oauth_session, auth_data["authorization_url"]

def exchange_code_for_token(client_id,client_secret,code,code_verifier):
    token_url = "http://127.0.0.1:8000/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": "http://127.0.0.1:9000/callback", # prove that we're using the same redirect URI during code exchange.
        "code_verifier": code_verifier,
    }
    response = requests.post(token_url,data)
    response.raise_for_status()
    return response.json()



''' 
Step 1 — AEP creates a secret

    - This line: code_verifier = secrets.token_urlsafe(32)

    - basically means: "Generate a random secret for me."

    - Imagine AEP generates: code_verifier = ABC123

    - Only AEP knows ABC123.


Step 2 — AEP creates a public-looking version of that secret

    - Now we have: ABC123
    - But we don't want to send ABC123 directly to the authorization server.
    - Instead, we create another value from it. That's the code_challenge.
    - Conceptually:

        ABC123
        ↓
        transform it
        ↓
        XYZ789

    - So:

        code_verifier  = ABC123   ← secret, AEP keeps it
        code_challenge = XYZ789   ← send this to OAuth server

Step 3 — Why do this?

        When AEP starts authorization, it says:

        "OAuth server, I'm AEP. Please authorize me. Here's my challenge."

        AEP
        │
        │  client_id = AEP
        │  code_challenge = XYZ789
        ▼
        OAuth Server

        The OAuth server remembers:

        AEP → XYZ789

Step 4 — User authorizes

            - The user approves access.
            - OAuth server gives AEP:
            - authorization_code = 123456

Step 5 — AEP comes back with the code AND its secret

      - Now AEP says:
            Here is my authorization code: 123456
            And here is my secret: ABC123

      - The OAuth server takes ABC123, performs the same transformation, and checks:

         ABC123
            ↓
        transform
            ↓
        XYZ789

            It compares:

            What I received earlier: XYZ789
            What I calculated now:   XYZ789

✅ Match → AEP is allowed to continue.
'''