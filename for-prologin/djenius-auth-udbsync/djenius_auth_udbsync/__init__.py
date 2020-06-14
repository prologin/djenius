import threading
from typing import Optional

import prologin.udbsync.client

from djenius.auth import AuthProvider
from djenius.proto import User, Ability, UserId


class UdbSyncAuthProvider(AuthProvider):
    def __init__(self):
        self.users = {}
        self.lock = threading.Lock()

    async def init(self):
        # TODO: once the udbsync async client is available, use it instead of that crap.
        t = threading.Thread(target=self.poll_udbsync_forever)
        t.daemon = True
        t.start()

    def poll_udbsync_forever(self):
        def callback(users, updates_metadata):
            with self.lock:
                self.users = {
                    login: User(id=login, abilities=get_abilities(user["group"]))
                    for login, user in users.items()
                }

        prologin.udbsync.client.connect().poll_updates(callback)

    def get_user_id(self, request) -> Optional[UserId]:
        return request.headers.get("X-SSO-User")

    def get_user(self, user_id: Optional[UserId]) -> Optional[User]:
        with self.lock:
            return self.users.get(user_id)


def get_abilities(group):
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
