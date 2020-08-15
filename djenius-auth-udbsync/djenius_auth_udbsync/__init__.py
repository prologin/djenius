import threading
from typing import Optional, Set

import prologin.udbsync.client

from djenius.auth import AuthProvider
from djenius.proto import Ability, UserId, User


def get_abilities(group: str) -> Set[Ability]:
    """Translates a Prologin group (user, orga, root) to a capability set."""
    user = {Ability.search, Ability.suggest, Ability.up_vote, Ability.down_vote}
    orga = {Ability.ban, Ability.accept}
    root = {
        Ability.volume,
        Ability.pause,
        Ability.skip,
        Ability.seek,
        Ability.admin_queue,
    }
    return {"user": user, "orga": user | orga, "root": user | orga | root}.get(
        group, set()
    )


class UdbSyncAuthProvider(AuthProvider):
    """AuthProvider that listens for Prologin udb updates.

    It relies on Prologin SSO, ie. the X-SSO-User header must be present.
    It maintains a mapping to make retrievals cheap."""

    def __init__(self):
        self.users = {}
        self.lock = threading.Lock()

    async def init(self):
        # TODO: once the udbsync async client is available, use it instead of that crap.
        t = threading.Thread(target=self._poll_udbsync_forever)
        t.daemon = True
        t.start()

    def get_user_id(self, request) -> Optional[UserId]:
        return request.headers.get("X-SSO-User")

    def get_user(self, user_id: Optional[UserId]) -> Optional[User]:
        with self.lock:
            return self.users.get(user_id)

    def _poll_udbsync_forever(self):
        def callback(users, updates_metadata):
            with self.lock:
                self.users = {
                    login: User(id=login, abilities=get_abilities(user["group"]))
                    for login, user in users.items()
                }

        prologin.udbsync.client.connect().poll_updates(callback)
