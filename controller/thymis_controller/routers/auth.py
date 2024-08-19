from typing import Annotated, Dict
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from thymis_controller.config import global_settings
from thymis_controller.dependencies import (
    SessionAD,
    apply_user_session,
    get_user_session_id,
    invalidate_user_session,
    require_valid_user_session,
)


class AuthMethods(BaseModel):
    basic: bool
    oauth2: bool


REDIRECT_URI = global_settings.BASE_URL + "/auth/callback"

router = APIRouter(
    tags=["auth"],
)


# only enable basic auth if the flag is set
@router.post("/login/basic")
def login_basic(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    redirect: Annotated[str, Form()],
    response: Response,
    db_session: SessionAD,
):
    if not global_settings.AUTH_BASIC:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Basic auth is disabled"
        )

    assert urlparse(redirect).netloc == "" and not urlparse(redirect).scheme

    if (
        username == global_settings.AUTH_BASIC_USERNAME
        and password == global_settings.AUTH_BASIC_PASSWORD
    ):  # TODO replace password check with hash comparison
        apply_user_session(db_session, response)
        return RedirectResponse(
            redirect, headers=response.headers, status_code=status.HTTP_303_SEE_OTHER
        )
    else:
        return RedirectResponse(
            f"/login?redirect={redirect}&authError=credentials",
            headers=response.headers,
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.get("/auth/methods", response_model=AuthMethods)
def get_auth_methods():
    return AuthMethods(
        basic=global_settings.AUTH_BASIC, oauth2=global_settings.AUTH_OAUTH
    )


# Route to redirect user to the OAuth2 provider's authorization URL
@router.get("/login/oauth2")
def login():
    return RedirectResponse(
        f"{global_settings.AUTH_OAUTH_AUTHORIZATION_ENDPOINT}?response_type=code&client_id={global_settings.AUTH_OAUTH_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid profile email"
    )


@router.post("/logout")
def logout(
    response: Response,
    user_session: Annotated[str, Depends(get_user_session_id)],
    db_session: SessionAD,
):
    invalidate_user_session(db_session, response, user_session)


# Route to handle the OAuth2 provider's callback
@router.get("/callback")
async def callback(code: str, response: Response, db_session: SessionAD):
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token exchange failed"
        )

    # token_data = token_response.json() to be used in the future

    apply_user_session(db_session, response)
    return RedirectResponse(
        "/", headers=response.headers, status_code=status.HTTP_303_SEE_OTHER
    )  # necessary to set the cookies


@router.get("/protected")  # TODO remove debug route
def read_protected(loggedin: Annotated[Dict, Depends(require_valid_user_session)]):
    return {"message": "You are logged in"}
