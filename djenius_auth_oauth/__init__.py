import logging
import os
import threading
import aiohttp
import jwt

from typing import Optional, Set
from base64 import b64decode

from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography.hazmat.primitives import serialization
from aiohttp_session import get_session, setup as session_setup
from aiohttp import web, ClientSession, FormData

from djenius.auth import AuthProvider
from djenius.proto import Ability, UserId, User
from yarl import URL

logger = logging.getLogger(__name__)

CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET", "")
CONFIG_URL = os.getenv("OIDC_CONFIG_URL", "")
# Can generate whit cryptography.fernet.Fernet.generate_key()
COOKIE_SESSION_KEY = os.getenv("COOKIE_SESSION_KEY")
SCOPES = ["openid", "profile", "email", "roles"]


def get_abilities(groups) -> Set[Ability]:
    """Translates a Prologin Final group to a capability set."""
    user = {Ability.search, Ability.suggest, Ability.up_vote, Ability.down_vote}
    orga = {Ability.ban, Ability.accept} | user
    root = {
               Ability.volume,
               Ability.pause,
               Ability.skip,
               Ability.seek,
               Ability.admin_queue,
           } | orga
    if "roots" in groups or "djenius-roots" in groups:
        return root
    if "bureau" in groups:
        return orga | {Ability.admin_queue, }
    if "staff-finale" in groups or "serveur" in groups:
        return orga
    if "staff" in groups or "contestants" in groups:
        return user
    return set()


async def client_session(app: web.Application):
    async with ClientSession() as session:
        app["session"] = session
        yield


async def logout(request: web.Request):
    session = await get_session(request)
    session.invalidate()
    return web.HTTPTemporaryRedirect(location="/")


class OauthAuthProvider(AuthProvider):

    def __init__(self):
        self.base_oidc_url = None
        self.public_key = None
        self.realm = None
        self.users = {}
        self.lock = threading.Lock()

    def pre_init(self, app: 'aiohttp.web.Application'):
        session_setup(app, EncryptedCookieStorage(COOKIE_SESSION_KEY))
        app.cleanup_ctx.append(client_session)
        app.add_routes([web.get("/auth/prologin/auth", self.on_auth_view),
                        web.get("/auth/prologin/callback", self.on_auth_callback),
                        web.get("/auth/prologin/logout", logout)])

    def get_login_path(self) -> Optional[str]:
        return "/auth/prologin/auth"

    def get_logout_path(self) -> Optional[str]:
        return "/auth/prologin/logout"

    async def init(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(CONFIG_URL) as resp:
                settings = await resp.json()

                key_der_base64 = settings["public_key"]
                key_der = b64decode(key_der_base64.encode())
                self.public_key = serialization.load_der_public_key(key_der)
                self.base_oidc_url = settings["token-service"]
                self.realm = settings["realm"]

    async def get_user_id(self, request) -> Optional[UserId]:
        session = await get_session(request)
        if "userid" in session:
            return session["userid"]
        return None

    def get_user(self, user_id: Optional[UserId]) -> Optional[User]:
        if user_id is None:
            return User(id=None, abilities=[])
        with self.lock:
            if user_id not in self.users:
                return User(id=None, abilities=[])
            return self.users.get(user_id)

    def get_claims(self, token):
        header_data = jwt.get_unverified_header(token)
        try:
            claims = jwt.decode(
                token,
                self.public_key,
                algorithms=[header_data['alg'], ],
                audience=CLIENT_ID,
                options={"verify_aud": False},
            )
        except jwt.PyJWTError as e:
            logger.warning("could not verify id_token sig: {}".format(e))
            return None
        return claims

    async def on_login(self, request: web.Request, prologin_token):
        """
        This function is called when the user is redirected back to the app after
        logging in with Prologin SSO. It sets the session and redirects to the
        original URL.
        """
        session = await get_session(request)
        data = self.get_claims(prologin_token['access_token'])

        user_id = data["preferred_username"]
        session["userid"] = user_id

        with self.lock:
            self.users[user_id] = User(id=user_id, abilities=get_abilities(data['realm_access']['roles']))
        return web.HTTPTemporaryRedirect(location="/")

    async def on_error(self, request: web.Request, error):
        logger.error("Error during OAuth2 flow: %s", error)
        return web.HTTPTemporaryRedirect(location="/")

    async def on_auth_view(self, request: web.Request):
        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": "http://192.168.8.76/auth/prologin/callback",
            "response_type": "code",
            "scope": " ".join(SCOPES),
        }
        return web.HTTPTemporaryRedirect(location=str(URL(f"{self.base_oidc_url}/auth").with_query(params)))

    async def on_auth_callback(self, request: web.Request):
        if request.query.get("error") is not None:
            return await self.on_error(request, request.query["error"])

        params = {"headers": {"Accept": "application/json"}}

        # noinspection PyTypeChecker
        params["data"] = FormData(tuple({
                                            "client_id": CLIENT_ID,
                                            "client_secret": CLIENT_SECRET,
                                            "code": request.query["code"],
                                            "redirect_uri": "http://192.168.8.76/auth/prologin/callback",
                                            "grant_type": "authorization_code",
                                        }.items()))

        async with request.app["session"].post(f"{self.base_oidc_url}/token", **params) as r:
            result = await r.json()

        return await self.on_login(request, result)
