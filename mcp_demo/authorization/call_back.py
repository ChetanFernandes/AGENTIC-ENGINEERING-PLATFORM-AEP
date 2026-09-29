from fastapi import FastAPI
import uvicorn
from mcp_demo.authorization.authorizationn.oauth_authorization import exchange_code_for_token


app = FastAPI()
access_token = None
oauth_session = {}

def set_oauth_session(session):
    global oauth_session
    oauth_session = session

@app.get("/callback")
async def call_back(code:str):
    global access_token
    token_response = exchange_code_for_token(
        client_id=oauth_session["client_id"],
        client_secret=oauth_session["client_secret"],
        code=code,
        code_verifier=oauth_session["code_verifier"],
    )

    access_token = token_response["access_token"]


    print("Access token received")

    return {
        "message": "Authorization successful. You can close this browser window."
    }

