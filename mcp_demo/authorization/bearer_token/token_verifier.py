from fastmcp.server.auth import TokenVerifier,AccessToken
class MyTokenVerifier(TokenVerifier):
    async def verify_token(self,token:str) -> AccessToken| None:
        if token == "my-secret-token":
            return AccessToken(token=token, client_id="aep_client",scopes =[])
        return None

    