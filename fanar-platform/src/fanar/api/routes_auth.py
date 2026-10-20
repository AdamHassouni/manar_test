"""BFF auth routes — authorization-code + PKCE against Keycloak, session in an httpOnly cookie.

The browser never receives tokens: `/login` redirects to Keycloak with a PKCE challenge; `/callback`
exchanges the code server-side and stores the tokens in the session store, handing back only an
opaque, httpOnly/secure/same-site session cookie. This closes review findings #1/#4/#5.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from fanar.api.deps import (get_oidc_client, get_session_store, get_settings, get_verifier,
                            require_principal)
from fanar.security.oidc import OidcClient
from fanar.security.pkce import generate_pkce, random_token
from fanar.security.sessions import SessionStore

router = APIRouter()
_LOGIN_COOKIE = "fanar_login"


@router.get("/login")
def login(oidc: OidcClient = Depends(get_oidc_client),
          sessions: SessionStore = Depends(get_session_store)) -> Response:
    verifier, challenge = generate_pkce()
    state = random_token()
    staging = sessions.create({"pkce_verifier": verifier, "state": state})
    url = oidc.authorization_url(state=state, code_challenge=challenge)
    resp = RedirectResponse(url, status_code=302)
    resp.set_cookie(_LOGIN_COOKIE, staging.id, httponly=True,
                    secure=get_settings().cookie_secure, samesite="lax", max_age=600)
    return resp


@router.get("/callback")
def callback(code: str, state: str, request: Request,
             oidc: OidcClient = Depends(get_oidc_client),
             sessions: SessionStore = Depends(get_session_store)) -> Response:
    login_sid = request.cookies.get(_LOGIN_COOKIE)
    staging = sessions.get(login_sid) if login_sid else None
    if not staging or staging.data.get("state") != state:
        raise HTTPException(status_code=400, detail="invalid or expired login state")

    tokens = oidc.exchange_code(code=code, code_verifier=staging.data["pkce_verifier"])
    principal = get_verifier().verify(tokens["access_token"])
    session = sessions.create({
        "tokens": tokens,
        "principal": {
            "subject": principal.subject, "username": principal.username,
            "tenant": principal.tenant, "roles": sorted(principal.roles),
        },
    })
    sessions.delete(staging.id)

    settings = get_settings()
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(settings.session_cookie_name, session.id, httponly=True,
                    secure=settings.cookie_secure, samesite="lax")
    resp.delete_cookie(_LOGIN_COOKIE)
    return resp


@router.post("/logout")
def logout(request: Request, sessions: SessionStore = Depends(get_session_store)) -> Response:
    settings = get_settings()
    sid = request.cookies.get(settings.session_cookie_name)
    if sid:
        sessions.delete(sid)
    resp = Response(status_code=204)
    resp.delete_cookie(settings.session_cookie_name)
    return resp


@router.get("/me")
def me(principal=Depends(require_principal)) -> dict:
    return {"username": principal.username, "tenant": principal.tenant,
            "roles": sorted(principal.roles)}
