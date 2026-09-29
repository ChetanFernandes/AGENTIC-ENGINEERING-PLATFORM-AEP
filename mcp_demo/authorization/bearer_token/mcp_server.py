from fastmcp import FastMCP
from mcp_demo.authorization.bearer_token.token_verifier import MyTokenVerifier
from fastmcp.server.auth import OAuthProvider
from mcp.server.auth.settings import ClientRegistrationOptions
import secrets
import time
from mcp.server.auth.provider import AuthorizationCode, AccessToken, OAuthToken

class AEPAuthProvider(OAuthProvider):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.clients = {}
        self.authorization_codes = {}
        self.access_tokens = {}

    async def register_client(self, client_info):
        print(">>> REGISTER CLIENT:", client_info.client_id)
        self.clients[client_info.client_id] = client_info
        print(">>> STORED CLIENTS:", list(self.clients.keys()))


    async def get_client(self, client_id):
        print(">>> GET CLIENT:", client_id)
        print(">>> STORED CLIENTS:", list(self.clients.keys()))
        return self.clients.get(client_id)


    async def authorize(self, client, params):

        code = secrets.token_urlsafe(32)

        authorization_code = AuthorizationCode(
            code=code,
            scopes=params.scopes or [],
            expires_at=time.time() + 300,
            client_id=client.client_id,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            resource=params.resource,
        )

        self.authorization_codes[code] = authorization_code

        return f"{params.redirect_uri}?code={code}"

    async def load_authorization_code(self, client, authorization_code):
        ''' find/validate the authorization code '''    

        return self.authorization_codes.get(authorization_code)

    async def exchange_authorization_code(self, client, authorization_code):
        ''' Turns code into access token'''
        access_token = secrets.token_urlsafe(32)

        self.access_tokens[access_token] = AccessToken(
            token=access_token,
            client_id=client.client_id,
            scopes=authorization_code.scopes,
            expires_at=int(time.time()) + 3600,
        )

        return OAuthToken(
            access_token=access_token,
            token_type="Bearer",
            expires_in=3600,
        )

    async def load_access_token(self, token):
        ''' An MCP request arrived with this Bearer token. Do I recognize this token?” '''

        print(">>> LOAD ACCESS TOKEN:", token)

        access_token = self.access_tokens.get(token)

        print(">>> ACCESS TOKEN FOUND:", access_token is not None)

        return access_token
    
oauth = AEPAuthProvider(base_url="http://127.0.0.1:8000", client_registration_options=ClientRegistrationOptions(enabled=True)) 
# Allow OAuth clients such as our AEP to register themselves."
# client_registration_options=ClientRegistrationOptions(enabled=True) - Turns ON /register

#verifier = MyTokenVerifier()

mcp = FastMCP("streameable HTTP MCP",auth = oauth) 

@mcp.tool(annotations={"destructive_hint":True})
def add(a:int,b:int)-> int:
    """Add two numbers."""
    return a + b

@mcp.tool(annotations={"readOnlyHint": True})
def get_user() -> dict:
    """user look up"""
    return {
        "name": "Chetan",
        "role": "Project Manager",
        "skills": ["AI", "LangGraph", "MCP"]
    }


if __name__=="__main__":
    mcp.run(transport="http",host= "127.0.0.1", port = 8000)

    

'''
authorization_endpoint → /authorize
token_endpoint         → /token
grant_types            → authorization_code, refresh_token
response_types         → code
code_challenge         → S256
'''

# FASTMCP - Authorization Server(OAUth authorization server or Oauth server)
# Oauth client - AEP
''' 
OAuth terminology

AEP
 ↓
OAuth Client

FastMCP OAuthProvider
 ↓
Authorization Server

MCP tools
 ↓
Protected Resource
'''
''' 
The OAuth server needs information about AEP, such as:

client_name
redirect_uri
grant_types
response_types
'''

#OAuth Authorization Server → the role
#FastMCP OAuthProvider → the component implementing that role
#FastMCP server → the actual server/application running it