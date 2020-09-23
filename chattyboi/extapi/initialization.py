import asyncio
from typing import Awaitable, Callable

from qasync import asyncSlot

from .types import Chat, Message
from ._state import state

__all__ = ('register_chat', 'on_ready', 'always_run', 'on_message', 'on_cleanup')


def register_chat(chat: Chat):
	"""
	Register a Chat so that it gets integrated with the rest of ChattyBoi. This takes care of adding it to the state
	and connecting all of the necessary signals.
	"""
	state().add_chat(chat)


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
