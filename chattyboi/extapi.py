import asyncio
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

mod = _types.SimpleNamespace(
	chattyboi=chattyboi,
	config=config,
	gui=gui,
	profiles=profiles,
	utils=utils
)


def state():
	return _state.state


def on_ready(coro):
	state().ready.connect(asyncSlot()(coro))
	return coro


def always_run(interval=1):
	def deco(coro):
		async def repeat():
			while asyncio.get_event_loop().is_running():
				await coro()
				await asyncio.sleep(interval)
		state().ready.connect(lambda: asyncio.get_event_loop().create_task(repeat()))
	return deco


def on_message(coro):
	state().anyMessageReceived.connect(asyncSlot(Message)(coro))
	return coro


def on_cleanup(coro):
	state().cleanup.connect(asyncSlot()(coro))
	return coro


def log(message, level='INFO'):
	chattyboi.logger.log(getattr(logging, level.upper()), message)


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


def self_user():
	return state().database.self_user()
