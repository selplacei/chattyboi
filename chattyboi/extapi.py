import types as _types
import typing

import chattyboi
import config
import gui
import profiles
import state as _state
import utils


Extension = chattyboi.Extension
User = chattyboi.User
Message = chattyboi.Message
Chat = chattyboi.Chat

modules = _types.SimpleNamespace(
	chattyboi=chattyboi,
	config=config,
	gui=gui,
	profiles=profiles,
	utils=utils
)


def state():
	return _state.state


def on_ready(slot):
	chattyboi.delayed_connect_event_slots['ready'].append(slot)


def add_extension_alias(source, name):
	extension = get_extension(source)
	if extension is None:
		raise ValueError(f'The extension [{source}] does not exist')
	if (test_duplicate := get_extension(name)) and test_duplicate != extension:
		raise ValueError(f'An extension with the name or alias {name} already exists')
	extension.add_alias(name)


def get_extension(identifier: str) -> typing.Optional[Extension]:
	"""
	Get an Extension object that matches the identifier and is loaded into the state.
	Useful for retrieving the current extension, i.e. `get_extension(__name__)`.

	:param identifier: a source, a name, an alias, or a module name
	:returns: Extension object if found, None otherwise
	"""
	return next((candidate for candidate in state().extensions if identifier in candidate.aliases), None)


def register_chat(chat: Chat):
	state().chats.add(chat)
	chat.messageReceived.connect(state().anyMessageReceived.emit)
