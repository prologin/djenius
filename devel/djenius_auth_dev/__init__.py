from typing import Optional

from djenius.auth import AuthProvider
from djenius.proto import UserId, Ability, User


class DevAuthProvider(AuthProvider):
    def get_user_id(self, request) -> Optional[UserId]:
        return request.cookies.get("dev_userid")

    def get_user(self, user_id: Optional[UserId]) -> Optional[User]:
        user = {Ability.search, Ability.up_vote, Ability.down_vote, Ability.suggest}
        staff = {Ability.ban, Ability.accept} | user
        root = {
            Ability.pause,
            Ability.skip,
            Ability.seek,
            Ability.admin_queue,
            Ability.volume,
        } | staff
        abilities = {"root": root, "staff": staff, "user": user}.get(user_id, set())
        return User(id=user_id, abilities=abilities)
