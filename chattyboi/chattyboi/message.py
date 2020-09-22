# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import collections
import datetime
from typing import Optional, TypeVar, Generic

from PySide2.QtCore import QObject

import chattyboi

MessageContent = TypeVar('MessageContent', collections.UserString, str, bytes)


class Message(QObject, Generic[MessageContent]):
	"""
	Represents a single message.
	A message with `None` as the source can be useful for debugging if the bot doesn't need to send a response.
	"""
	
	def __init__(self, source: Optional[chattyboi.Chat], author: chattyboi.User, content: MessageContent, timestamp=None):
		super().__init__(None)
		self.source = source
		self.author = author
		self.content: MessageContent = content
		self.timestamp = timestamp or datetime.datetime.now().timestamp()
	
	def __str__(self):
		return str(self.content)
	
	async def respond(self, *args, **kwargs):
		await self.source.send(*args, **kwargs)
	
	async def reply(self, *args, **kwargs):
		await self.source.send_to(*args, **kwargs, users=[self.author])
