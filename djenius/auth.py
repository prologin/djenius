import abc
from typing import Optional
from aiohttp import web

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

    async def init(self):
        pass

    @abc.abstractmethod
    def get_user_id(self, request: web.Request) -> Optional[UserId]:
        """
        Returns a user ID for the given request, or None.
        """
        ...

    @abc.abstractmethod
    def get_user(self, user_id: Optional[UserId]) -> Optional[User]:
        """
        Returns a :class:`User` for the given user id, or None.
        """
        ...
