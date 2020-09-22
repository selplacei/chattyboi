# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import datetime
import logging
from typing import List, Optional

from PySide2.QtCore import Signal, QObject
from PySide2.QtWidgets import QApplication

import gui
import profiles

from . import Chat, Extension, ExtensionHelper, Message


class ApplicationState(QObject):
	"""
	Data structure that describes the state of a ChattyBoi application.
	The following information can be retrieved using this class:
		* main ChattyBoi logger;
		* current profile;
		* loaded extensions;
		* associated ExtensionHelper;
		* associated DatabaseWrapper;
		* active chat streams;
		* start time and uptime;
		* the main GUI window.
	"""
	ready = Signal()
	cleanup = Signal()
	chatAdded = Signal(Chat)
	anyMessageReceived = Signal(Message)
	anyMessageSent = Signal(str)
	
	def __init__(self, logger, profile, extensions=None, chats=None, main_window=None):
		super().__init__(None)
		QApplication.instance().aboutToQuit.connect(self.cleanup)
		self.profile: profiles.Profile = profile
		self.logger: logging.Logger = logger
		self.extensions: List[Extension] = extensions or []
		self.chats: List[Chat] = chats or []
		self.main_window: Optional[gui.windows.MainWindow] = main_window
		self.start_time: Optional[datetime.datetime] = None
		self.extension_helper = ExtensionHelper(self)
		self.ready.connect(self._on_ready)
	
	def _on_ready(self):
		self.start_time = datetime.datetime.now()
	
	@property
	def database(self):
		return self.profile.db_connection
	
	@property
	def uptime(self) -> datetime.timedelta:
		return datetime.datetime.now() - self.start_time
	
	def find_extension_by_module(self, module) -> Extension:
		return next(ext for ext in self.extensions if ext.module is module)
	
	def add_chat(self, chat):
		self.chats.append(chat)
		self.chats.sort(key=lambda c: str(c))
		chat.messageReceived.connect(self.anyMessageReceived)
		self.chatAdded.emit(chat)
