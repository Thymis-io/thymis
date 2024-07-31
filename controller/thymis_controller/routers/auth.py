import datetime
from typing import Annotated, Dict
import uuid
from fastapi import APIRouter, FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import httpx
from pydantic import BaseModel
from thymis_controller.config import global_settings
from thymis_controller.dependencies import SessionTicket, get_session, require_valid_session, apply_session, invalidate_session

class AuthMethods(BaseModel):
    basic: bool
    oauth2: bool

REDIRECT_URI = global_settings.BASE_URL + "/auth/callback"

router = APIRouter(
    tags=["auth"],
)
basicAuth = HTTPBasic()

# only enable basic auth if the flag is set
@router.post("/login/basic")
def login_basic(credentials: Annotated[HTTPBasicCredentials, Depends(basicAuth)], response: Response):
    if not global_settings.AUTH_BASIC_ENABLED:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Basic auth is disabled")
    if credentials.username == global_settings.AUTH_BASIC_USERNAME and credentials.password == global_settings.AUTH_BASIC_PASSWORD: # TODO replace password check with hash comparison
        apply_session(response, None)
        return {"message": "Logged in"}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@router.get("/auth/methods", response_model=AuthMethods)
def get_auth_methods():
    return AuthMethods(basic=global_settings.AUTH_BASIC, oauth2=global_settings.AUTH_OAUTH)

# Route to redirect user to the OAuth2 provider's authorization URL
@router.get("/login/oauth2")
def login():
    return RedirectResponse(
        f"{global_settings.AUTH_OAUTH_AUTHORIZATION_ENDPOINT}?response_type=code&client_id={global_settings.AUTH_OAUTH_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid profile email"
    )

@router.post("/logout")
def logout(response: Response, session: Annotated[SessionTicket, Depends(require_valid_session)]):
    invalidate_session(response)
    return {"message": "Logged out"}

# Route to handle the OAuth2 provider's callback
@router.get("/callback")
async def callback(code: str, response: Response):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            global_settings.AUTH_OAUTH_TOKEN_ENDPOINT,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": global_settings.AUTH_OAUTH_CLIENT_ID,
                "client_secret": global_settings.AUTH_OAUTH_CLIENT_SECRET,
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token exchange failed")

    token_data = token_response.json()
    apply_session(response, token_data["access_token"])
    return RedirectResponse("/", headers=response.headers) # necessary to set the cookies

@router.get("/protected") # TODO remove debug route
def read_protected(token: Annotated[Dict, Depends(require_valid_session)]):
    return {"message": "Hello World"}
