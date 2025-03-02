import json
import pathlib
from typing import Annotated, Optional
from urllib.parse import quote, unquote

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from thymis_controller.config import global_settings
from thymis_controller.dependencies import (
    DBSessionAD,
    LoginRedirectCookieAD,
    UserSessionIDAD,
    UserSessionTokenAD,
    apply_user_session,
    get_user_session_token,
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
    redirect: Annotated[Optional[str], Form()],
    response: Response,
    db_session: DBSessionAD,
    redirect_cookie: LoginRedirectCookieAD = None,
):
    if not global_settings.AUTH_BASIC:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Basic auth is disabled"
        )

    # check for redirect in cookie
    redirect_url = None
    if redirect is not None and redirect_cookie is not None:
        # look for uuid in cookie[uuid], but first urldecode and jsondecode
        redirect_cookie = unquote(redirect_cookie)
        redirect_dict = json.loads(redirect_cookie)
        redirect_url = redirect_dict.get(redirect)
    if redirect_url is None:
        redirect_url = "/overview"

    password_file = pathlib.Path(global_settings.AUTH_BASIC_PASSWORD_FILE)
    password_file_content = password_file.read_text(encoding="utf-8").strip()

    if (
        username == global_settings.AUTH_BASIC_USERNAME
        and password == password_file_content
    ):  # TODO replace password check with hash comparison
        apply_user_session(db_session, response)
        # return RedirectResponse(
        #     redirect_url, headers=response.headers, status_code=status.HTTP_303_SEE_OTHER
        # )
        # return 200 with http-equiv refresh
        response.media_type = "text/html"
        response.status_code = status.HTTP_200_OK
        response.body = f'<!doctype html><meta charset=utf-8><title>Login successful</title><meta http-equiv="refresh" content="0; url=\'{redirect_url}\'"><body>Login successful'.encode(
            "utf-8"
        )
        return response
    else:
        return RedirectResponse(
            f"/login?redirect={quote(redirect)}&authError=credentials",
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


@router.get("/logout")
def logout(
    response: Response,
    user_session_id: UserSessionIDAD,
    user_session_token: UserSessionTokenAD,
    db_session: DBSessionAD,
):
    invalidate_user_session(db_session, response, user_session_id, user_session_token)
    return RedirectResponse(
        "/", headers=response.headers, status_code=status.HTTP_303_SEE_OTHER
    )


# Route to handle the OAuth2 provider's callback
@router.get("/callback")
async def callback(code: str, response: Response, db_session: DBSessionAD):
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


@router.get("/logged_in")
def read_protected(loggedin: Annotated[bool, Depends(require_valid_user_session)]):
    assert loggedin
    return {"message": "You are logged in"}
