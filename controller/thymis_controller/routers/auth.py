import pathlib
from typing import Annotated, Optional
from urllib.parse import quote, unquote

import httpx
import jwt
from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from thymis_controller.config import global_settings
from thymis_controller.crud import web_session
from thymis_controller.dependencies import (
    DBSessionAD,
    LoginRedirectCookieAD,
    UserSessionIDAD,
    UserSessionTokenAD,
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


def apply_user_session(db_session: DBSessionAD, response: Response):
    user_session = web_session.create(db_session)
    is_using_https = (
        global_settings.BASE_URL.startswith("https")
        or global_settings.BASE_URL.startswith("http://localhost")
        or global_settings.BASE_URL.startswith("http://127.0.0.1")
    )
    response.set_cookie(
        key="session-id",
        value=str(user_session.id),
        httponly=True,
        secure=is_using_https,
        samesite="lax",
        expires=web_session.SESSION_LIFETIME_SECONDS,
        max_age=web_session.SESSION_LIFETIME_SECONDS,
    )
    response.set_cookie(
        key="session-token",
        value=user_session.session_token,
        httponly=True,
        secure=is_using_https,
        samesite="lax",
        expires=web_session.SESSION_LIFETIME_SECONDS,
        max_age=web_session.SESSION_LIFETIME_SECONDS,
    )


def parse_redirect_cookie(
    redirect_cookie: Optional[str], expected_key: Optional[str]
) -> Optional[str]:
    if not redirect_cookie or not expected_key:
        return None
    # redirect_cookie: "{key}-{url}"
    parts = unquote(redirect_cookie).split("-", 1)
    if len(parts) == 2 and expected_key == parts[0] and parts[1].startswith("/"):
        return parts[1]
    return None


# only enable basic auth if the flag is set
@router.post("/login/basic")
def login_basic(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    response: Response,
    db_session: DBSessionAD,
    redirect: Annotated[Optional[str], Form()] = None,
    redirect_cookie: LoginRedirectCookieAD = None,
):
    if not global_settings.AUTH_BASIC:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Basic auth is disabled"
        )

    # check for redirect in cookie
    redirect_url = parse_redirect_cookie(redirect_cookie, redirect)
    if redirect_url:
        safe_redirect = redirect
    else:
        safe_redirect = None

    password_file = pathlib.Path(global_settings.AUTH_BASIC_PASSWORD_FILE)
    password_file_content = password_file.read_text(encoding="utf-8").strip()

    if (
        username == global_settings.AUTH_BASIC_USERNAME
        and password == password_file_content
    ):  # TODO replace password check with hash comparison
        apply_user_session(db_session, response)
        return RedirectResponse(
            "/auth/redirect_success"
            + (f"?redirect={quote(safe_redirect)}" if safe_redirect else ""),
            headers=response.headers,
            status_code=status.HTTP_303_SEE_OTHER,
        )
    else:
        if safe_redirect is not None:
            return RedirectResponse(
                f"/login?redirect={quote(safe_redirect)}&authError=credentials",
                headers=response.headers,
                status_code=status.HTTP_303_SEE_OTHER,
            )
        return RedirectResponse(
            "/login?authError=credentials",
            headers=response.headers,
            status_code=status.HTTP_303_SEE_OTHER,
        )


@router.get("/redirect_success")
def redirect_success(
    response: Response,
    loggedin: Annotated[bool, Depends(require_valid_user_session)],
    redirect: Optional[str] = None,
    redirect_cookie: LoginRedirectCookieAD = None,
    user_session_id: UserSessionIDAD = None,
    user_session_token: UserSessionTokenAD = None,
):
    assert loggedin
    # check for redirect in cookie
    redirect_url = parse_redirect_cookie(redirect_cookie, redirect)
    if redirect_url is None:
        redirect_url = "/overview"

    # set login cookies to strict
    response.set_cookie(
        key="session-id",
        value=str(user_session_id),
        httponly=True,
        secure=global_settings.BASE_URL.startswith("https"),
        samesite="strict",
        expires=web_session.SESSION_LIFETIME_SECONDS,
        max_age=web_session.SESSION_LIFETIME_SECONDS,
    )
    response.set_cookie(
        key="session-token",
        value=user_session_token,
        httponly=True,
        secure=global_settings.BASE_URL.startswith("https"),
        samesite="strict",
        expires=web_session.SESSION_LIFETIME_SECONDS,
        max_age=web_session.SESSION_LIFETIME_SECONDS,
    )
    return RedirectResponse(
        redirect_url,
        status_code=status.HTTP_303_SEE_OTHER,
        headers=response.headers,
    )


@router.get("/auth/methods", response_model=AuthMethods)
def get_auth_methods():
    return AuthMethods(
        basic=global_settings.AUTH_BASIC, oauth2=global_settings.AUTH_OAUTH
    )


# Route to redirect user to the OAuth2 provider's authorization URL
@router.get("/login/oauth2")
def login(redirect: Optional[str] = None):
    redirect_safe = redirect if redirect and redirect.isalnum() else ""
    return RedirectResponse(
        f"{global_settings.AUTH_OAUTH_AUTHORIZATION_ENDPOINT}?response_type=code&client_id={global_settings.AUTH_OAUTH_CLIENT_ID}&redirect_uri={REDIRECT_URI}&state={redirect_safe}&scope=openid profile email"
    )


@router.get("/logout")
def logout(
    response: Response,
    db_session: DBSessionAD,
    user_session_id: UserSessionIDAD = None,
    user_session_token: UserSessionTokenAD = None,
):
    invalidate_user_session(db_session, response, user_session_id, user_session_token)
    return RedirectResponse(
        "/", headers=response.headers, status_code=status.HTTP_303_SEE_OTHER
    )


# Route to handle the OAuth2 provider's callback
@router.get("/callback")
async def callback(
    code: str, response: Response, db_session: DBSessionAD, state: Optional[str] = None
):
    secret_file = pathlib.Path(global_settings.AUTH_OAUTH_CLIENT_SECRET_FILE)
    secret_file_content = secret_file.read_text(encoding="utf-8").strip()
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            global_settings.AUTH_OAUTH_TOKEN_ENDPOINT,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": global_settings.AUTH_OAUTH_CLIENT_ID,
                "client_secret": secret_file_content,
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token exchange failed"
        )

    token_data = token_response.json()

    access_token = token_data.get("access_token")
    jwt_token = jwt.decode(
        access_token, options={"verify_signature": False}
    )  # TODO verify signature

    if not jwt_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )

    if global_settings.AUTH_OAUTH_CLIENT_ROLE_LOGIN:
        client_roles = jwt_token.get("resource_access").get(
            global_settings.AUTH_OAUTH_CLIENT_ID
        )
        if (
            not client_roles
            or global_settings.AUTH_OAUTH_CLIENT_ROLE_LOGIN
            not in client_roles.get("roles", [])
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have the required role",
            )

    apply_user_session(db_session, response)

    redirect_safe = state if state and state.isalnum() else ""
    return Response(
        content=f"""<!DOCTYPE html>
<html>
<head><meta http-equiv="refresh" content="0; url='/auth/redirect_success?redirect={redirect_safe}'"></head>
<body></body>
</html>""",
        media_type="text/html",
        headers=response.headers,
    )


@router.get("/logged_in")
def read_protected(loggedin: Annotated[bool, Depends(require_valid_user_session)]):
    assert loggedin
    return {"message": "You are logged in"}
