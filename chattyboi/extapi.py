import functools
import json
import logging
import types as _types
import typing

from qasync import asyncSlot

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


def on_ready(coro):
	chattyboi.delayed_connect_slots['on_ready'].append(asyncSlot()(coro))


def always_run(interval=1):
	def deco(coro):
		chattyboi.delayed_connect_slots['always_run'].append((coro, interval))
		return coro
	return deco


def on_message(coro):
	chattyboi.delayed_connect_slots['on_message'].append(asyncSlot(Message)(coro))
	return coro


def on_cleanup(coro):
	chattyboi.delayed_connect_slots['on_cleanup'].append(asyncSlot()(coro))
	return coro


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
	return next((ext for ext in state().extensions if identifier in ext.aliases), None)


def get_storage_path(extension):
	return state().profile.extension_storage_path / extension.hash


def register_chat(chat: Chat):
	state().add_chat(chat)


def get_user_data(extension, user):
	return user.extension_data.get(extension.hash, '{}')


def store_user_data(extension, user, data: dict):
	all_data = user.extension_data
	all_data.update({extension.hash: data})
	user.extension_data = all_data
