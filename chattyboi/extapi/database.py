from typing import Optional
from .types import User
from . import _state


__all__ = ('self_user', 'find_user', 'find_or_add_user')


def self_user() -> User:
	"""
	Get the self user. This can be useful for things like unlimited permissions, detection and ignoring of self-sent
	messages, or locally performing actions that require a User.

	The creation and management of the self user is done internally and should not be a responsibility of extensions,
	unless they also treat it in some special way.

	:return: The User object associated with the bot
	"""
	return _state().database.self_user()


def find_user(nickname) -> Optional[User]:
	return _state().database.find_user(nickname)


def find_or_add_user(nickname) -> User:
	return _state().database.find_or_add_user(nickname)
