import abc
from typing import Optional

import aiohttp
from djenius.proto import UserId, User


class AuthProvider(abc.ABC):
    """
    To provide authentication and authorization (through abilities), subclass
    this, implement the abstract methods with your logic (eg. reading from
    trusted headers in an SSO setup) and setup a Python package exposing your
    implementation.

    Make it available to Python path and then pass::

        --auth=module.path.of.my.impl
    """

    def pre_init(self, app: 'aiohttp.web.Application') -> None:
        pass

    async def init(self) -> None:
        pass

    def get_login_path(self) -> Optional[str]:
        return None

    def get_logout_path(self) -> Optional[str]:
        return None

    @abc.abstractmethod
    async def get_user_id(self, request: 'aiohttp.web.Request') -> Optional[UserId]:  # type: ignore
        """
        Returns a :class:`djenius.proto.UserId` for the given request, or None.
        """
        ...

    @abc.abstractmethod
    def get_user(self, user_id: Optional[UserId]) -> Optional[User]:
        """
        Returns a :class:`djenius.proto.User` for the given user id, or None.
        """
        ...
