# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import collections
from typing import List, Deque, Generic

from PySide2.QtCore import Signal, QObject

import state

from . import MessageContent, Message, User


class Chat(QObject, Generic[MessageContent]):
	"""
	Represents an API which can produce Message objects and to which content can be sent.
	Whenever a new message is received, `new_message()` should be called. Signals are handled automatically.
	"""
	messageReceived = Signal(Message)
	
	def __init__(self):
		super().__init__(None)
		self.messages: Deque[Message[MessageContent]] = collections.deque()
		self.name = 'Unknown'
	
	def __str__(self):
		return self.name
	
	def new_message(self, message: Message[MessageContent]):
		self.messages.append(message)
		self.messageReceived.emit(message)
		return message
	
	async def send_to(self, content: MessageContent, users: List[User]):
		await self.send(''.join(f'@{user.name} ' for user in users) + str(content))
	
	async def send(self, content: MessageContent):
		state.state.anyMessageSent.emit(str(content))
