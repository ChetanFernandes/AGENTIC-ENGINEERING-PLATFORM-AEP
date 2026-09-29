import threading
import time
import webbrowser
import uvicorn
from mcp_demo.authorization.call_back import app, set_oauth_session
from mcp_demo.authorization import call_back
from mcp_demo.authorization.authorizationn.oauth_authorization import create_oauth_session , preparing_authorization_request


def start_callback_server():
    uvicorn.run(app, host="127.0.0.1", port=9000)

def main():
    # Start callback server
    server_thread = threading.Thread(target=start_callback_server, daemon=True)
    server_thread.start()

    # "Start a receptionist in the background who waits at port 9000 for the OAuth server to deliver the authorization code. 
    # Meanwhile, I will continue with the OAuth process."

    # daemon=True
    #"Keep the callback server running in the background while I need it, but don't keep the "
    #"whole application alive after the main OAuth program is finished."

    time.sleep(1)

    # Step - 1 - Create OAuth session and register aep
    client_id, client_secret = create_oauth_session()

    # step - 2 - Prepare authorization request that has to be sent to FastMCP server by aep
    oauth_session, authorization_url = preparing_authorization_request(client_id, client_secret )

    # Step - 3 Give session information to callback server.
        # The callback server needs the session information because receiving the authorization code is not enough to get the access token.
        # To exchange that code for an access token, we also need:
            # client_id
            # client_secret
            # code_verifier
        # So the callback server needs the session.
        # Once authorization code is received. 
        # Callback server says, Here is the authorization code you gave me. I am client X, here is my credential, and here is my PKCE verifier. Give me the access token."# 
 
    set_oauth_session(oauth_session)

    # Step - 4 - Open the authorization URL in the user's browser.
    # This causes the browser to send a GET request to FastMCP's /authorize endpoint.
    # FastMCP validates the client and calls our authorize() method.
    # Our current authorize() implementation generates an authorization code
    # and redirects the browser to the callback URL.
    # Note: There is currently no user consent/approval page in our implementation.
    webbrowser.open(authorization_url)

    print("Waiting for OAuth authorization...")

    # Wait until callback receives access token
    # step - 4 - Once user approves, the FASTMCP server send the authorization code to callback url. 
    #  The Callback server will exchange code  for tokens
    #  The callback server receives the authorization code, and then the callback server (running as part of AEP) uses that code to request the access token
    
    while call_back.access_token is None:
        time.sleep(1)

    print("OAuth flow completed.")

    access_token = call_back.access_token

    return access_token

