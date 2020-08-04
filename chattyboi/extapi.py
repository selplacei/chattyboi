import asyncio
import logging
import types as _types
import inspect
import pathlib
from typing import Awaitable, Callable, Dict, Optional

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


def this() -> Extension:
	"""
	Get the extension from which this function was called.

	This should only be called from within extension code, i.e. where __name__ until the first dot is guaranteed to be
	the same as in the extension's __init__.py. Use this sparingly, preferably only in simple extensions, and directly
	from extension code. This assumes that __name__ wasn't overwritten.

	:return: Extension object if found, raising a RuntimeError otherwise
	:raise: RuntimeError if not found
	"""
	if e := get_extension(inspect.currentframe().f_back.f_globals['__name__'].split('.', 1)[0]):
		return e
	raise RuntimeError('this() must be called directly from within an extension (__init__.py or any submodule)')


def state():
	"""
	:return: The current global application state
	"""
	return _state.state


def on_ready(coro: Callable[[], Awaitable]):
	"""
	Decorator over async functions that will be executed on startup.

	Shorthand for ``state().ready.connect(asyncSlot()(coro))``
	"""
	state().ready.connect(asyncSlot()(coro))
	return coro


def always_run(interval=1):
	"""
	:param interval: Interval in seconds (default 1)
	:return: Decorator over an async function that will run repeatedly with the specified interval
	"""
	def deco(coro):
		async def repeat():
			while asyncio.get_event_loop().is_running():
				await coro()
				await asyncio.sleep(interval)
		state().ready.connect(lambda: asyncio.get_event_loop().create_task(repeat()))
	return deco


def on_message(coro: Callable[[Message], Awaitable]):
	"""
	Decorator over async functions that will be called with a ``Message`` as the argument when any message is received.

	Shorthand for ``state().anyMessageReceived.connect(asyncSlot()(coro))``
	"""
	state().anyMessageReceived.connect(asyncSlot(Message)(coro))
	return coro


def on_cleanup(coro):
	"""
	Decorator over async functions that will be executed on cleanup (graceful shutdown).

	Shorthand for ``state().cleanup.connect(asyncSlot()(coro))``
	"""
	state().cleanup.connect(asyncSlot()(coro))
	return coro


def log(message: str, level='INFO'):
	"""
	Log to the chattyboi logger. If your extension runs its own processing, it may make sense to use your own logger.
	The levels are the same as in the ``logging`` module.
	"""
	chattyboi.logger.log(getattr(logging, level.upper()), message)


def get_extension(identifier: str) -> Optional[Extension]:
	"""
	Get an Extension object that is loaded into the state and matches the identifier. It's highly encouraged to
	hardcode only the same identifiers as those used in the ``manifest.toml``'s ``requires`` field.

	:param identifier: a source, name, alias, or module name
	:return: Extension object if found, None otherwise
	"""
	return next((ext for ext in state().extensions if identifier in ext.aliases), None)


def register_chat(chat: Chat):
	"""
	Register a Chat so that it gets integrated with the rest of ChattyBoi. This takes care of adding it to the state
	and connecting all of the necessary signals.
	"""
	state().add_chat(chat)


def self_user() -> User:
	"""
	Get the self user. This can be useful for things like unlimited permissions, detection and ignoring of self-sent
	messages, or locally performing actions that require a User.

	The creation and management of the self user is done internally and should not be a responsibility of extensions,
	unless they also treat it in some special way.

	:return: The User object associated with the bot
	"""
	return state().database.self_user()
