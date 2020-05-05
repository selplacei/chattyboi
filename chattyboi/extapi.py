import logging
import types as _types
import typing

import qasync

import chattyboi
import config
import gui
import profiles
import state as _state
import utils


async_slot = qasync.asyncSlot
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
	chattyboi.delayed_connect_slots['on_ready'].append(slot)


def always_run(interval=1):
	def wrapper(coro):
		chattyboi.delayed_connect_slots['always_run'].append((coro, interval))
		return coro
	return wrapper


def on_message(slot):
	chattyboi.delayed_connect_slots['on_message'].append(slot)
	return slot


def on_cleanup(slot):
	chattyboi.delayed_connect_slots['on_cleanup'].append(slot)
	return slot


def log(message, level='INFO'):
	chattyboi.logger.log(getattr(logging, level.upper()), message)


def add_extension_alias(identifier, name):
	extension = get_extension(identifier)
	if extension is None:
		raise ValueError(f'The extension [{identifier}] does not exist')
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


def get_data_path(extension):
	return state().profile.extension_data_path / chattyboi.ExtensionHelper.get_hash(extension.source)


def register_chat(chat: Chat):
	state().add_chat(chat)
