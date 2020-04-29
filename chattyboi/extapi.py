import types as _types
import typing

import chattyboi
import config
import gui
import profiles
import utils
from state import state


types = _types.SimpleNamespace(
	User=chattyboi.User,
	Message=chattyboi.Message,
	Chat=chattyboi.Chat
)

modules = _types.SimpleNamespace(
	chattyboi=chattyboi,
	config=config,
	gui=gui,
	profiles=profiles,
	utils=utils
)


def add_extension_alias(source, name):
	extension = get_extension(source)
	if extension is None:
		raise ValueError(f'The extension [{source}] does not exist')
	if (test_duplicate := get_extension(name)) and test_duplicate != extension:
		raise ValueError(f'An extension with the name or alias {name} already exists')
	extension.add_alias(name)


def get_extension(identifier: str) -> typing.Optional[types.Extension]:
	"""
	Get an Extension object that matches the identifier and is loaded into the state.
	Useful for retrieving the current extension, i.e. `get_extension(__name__)`.

	:param identifier: a source, a name, an alias, or a module name
	:returns: Extension object if found, None otherwise
	"""
	return next((candidate for candidate in state.extensions if identifier in candidate.aliases), None)


def register_chat(chat: types.Chat):
	state.chats.add(chat)
	chat.messageReceived.connect(state.anyMessageReceived.emit)


def subscribe_to_messages(callback: callable):
	"""
	Subscribe to all messages, i.e. call `callback` any time a message is received.

	:param callback: callable that takes a Message as the argument
	"""
	state.anyMessageReceived.connect(callback)

