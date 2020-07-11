# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import collections
import datetime
import hashlib
import importlib.util
import itertools
import json
import logging
import pathlib
import sqlite3
import sys
from typing import List, Union, Tuple, Deque, Optional

import qasync
import toml
from PySide2.QtCore import Signal, QObject
from PySide2.QtWidgets import QApplication

import config
import gui
import profiles
import state
import utils

logging.basicConfig(
	format=config.log_format,
	datefmt=config.log_datefmt,
	level=config.log_level
)
logger = logging.getLogger('chattyboi')


class Extension:
	"""
	Information about a specific loaded extension.
	This only represents the info about it; its module is imported separately,
	and destroying this object will not unload the extension.

	The following information can be retrieved using this class:
		* metadata: accessed as normal attributes; they are listed as annotations in this class.
		* associated module: the `module` attribute.
		* public attributes of the module: accessed with `__get__`, i.e. as in a dict (extension['key']).
	"""
	name: str
	source: str
	author: str
	version: str
	source: str
	license: str
	summary: str
	description: str
	requires: List[str]
	implements: List[str]

	def __init__(self, metadata, hash, module):
		self.__dict__.update(metadata)
		self.hash = hash
		self.module = module
		self._aliases = set()

	def __eq__(self, other):
		return self.module is other.module

	def __hash__(self):
		return self.hash

	def __getitem__(self, item):
		if item in self.module.__all__:
			return getattr(self.module, item)

	@property
	def aliases(self):
		return {self.name, self.source, self.module.__name__, *self.implements} | self._aliases

	def add_alias(self, alias):
		self._aliases.add(alias)


class ExtensionHelper:
	"""
	Helper class for managing extensions associated with a specific state.
	To retrieve the list of needed extensions, the state's profile is used.
	When extensions are loaded, the state's `extensions` list is updated.

	The responsibilities of this class are as follows:
		* finding extension packages from a profile's properties;
		* parsing extension metadata;
		* building the extensions' dependency tree;
		* creating and loading extension modules;
		* initializing associated Extension objects;
		* updating the state's extension list.
	"""
	@staticmethod
	def get_metadata(fp: pathlib.Path, use_defaults=True):
		metadata = {
			'author': 'Unknown',
			'version': '<unknown>',
			'license': 'No license',
			'summary': 'No summary provided.',
			'description': 'No description provided.',
			'requires': [],
			'implements': []
		} if use_defaults else {}
		metadata.update(toml.load(fp))
		if 'name' not in metadata or 'source' not in metadata:
			raise RuntimeError(f'Extension metadata at {fp} does not provide a name and a source')
		return metadata

	@staticmethod
	def get_hash(source):
		return hashlib.md5(bytes(source, "utf-8")).hexdigest()

	@staticmethod
	def load_order(extensions: List[Tuple[pathlib.Path, dict]]) -> List[pathlib.Path]:
		"""
		Use Kahn's topological sort algorithm to find an extension load order that satisfies all dependencies.
		Assumes no duplicate implementations. A RuntimeError will be raised if there is a dependency cycle.
		"""
		order = []
		graph = {path: [] for path, _ in extensions}
		for path_u, info_u in extensions:
			for path_v, info_v in filter(lambda e: e[0] != path_u, extensions):
				if any(req == info_v['source'] or req in info_v['implements'] for req in info_u['requires']):
					graph[path_u].append(path_v)
		queue = [u for u, v in graph.items() if len(v) == 0]
		while queue:
			n = queue.pop()
			order.append(n)
			for m in (node for node, edges in graph.items() if n in edges):
				graph[m].remove(n)
				if len(graph[m]) == 0:
					queue.append(m)
		if any(edges for node, edges in graph.items()):
			raise RuntimeError(
				f'Encountered a dependency cycle when finding the load order. '
				f'These extensions probably caused the error:\n{graph}'
			)
		return order

	def __init__(self, state):
		self.state = state

	def load(self, path, metadata, module_name=None):
		hash = self.get_hash(metadata['source'])
		module_name = module_name or 'cbext_' + hash
		spec = importlib.util.spec_from_file_location(module_name, path / '__init__.py')
		module = importlib.util.module_from_spec(spec)
		sys.modules[module_name] = module
		extension = Extension(metadata, hash, module)
		self.state.extensions.append(extension)
		spec.loader.exec_module(module)

	def load_all(self):
		# TODO: use a config variable instead of a hardcoded extension directory
		paths = list((pathlib.Path('./extensions') / name) for name in self.state.profile.extensions)
		metadata = [self.get_metadata(fp / 'manifest.toml') for fp in paths]
		implementations = {md['source']: {md['source']} | set(md['implements']) for md in metadata}
		implemented = set()
		for i in implementations.values():
			implemented.update(i)
		dependencies = {md['name']: set(md['requires']) for md in metadata}
		for ext, deps in dependencies.items():
			for dep in deps:
				if dep not in implemented:
					raise RuntimeError(f'Dependency [{dep}] not satisfied for extension [{ext}]')
		for left, right in filter(lambda src: src[0] != src[1], itertools.product(implementations.keys(), repeat=2)):
			if conflicts := implementations[left] & implementations[right]:
				raise RuntimeError(
					f'Duplicate extension implementations found:'
					f'Both [{left}] and [{right}] implement {conflicts}'
				)
		for path in self.load_order(zip(paths, metadata)):
			self.load(path, metadata[paths.index(path)])


class DatabaseWrapper:
	"""
	Wrapper around a profile's SQLite3 database that provides ChattyBoi-specific helper functions.
	"""
	SELF_NICKNAME = 'self'

	def __init__(self, source: pathlib.Path, connection: sqlite3.Connection):
		self.source = source
		self.connection = connection

	def __eq__(self, other):
		return self.source == other.source

	def __hash__(self):
		return id(self)

	def cursor(self):
		return self.connection.cursor()

	def commit(self):
		self.connection.commit()

	def self_user(self):
		return self.find_or_add_user(self.SELF_NICKNAME)

	def add_user(self, nicknames, extension_data: Union[str, dict] = None) -> int:
		"""
		Add a new user entry to the database and return its row ID if successful.
		If any of the nicknames already exist, this will raise a ValueError.
		"""
		for nickname in nicknames:
			if self.find_user(nickname):
				raise ValueError(f'A user with the nickname "{nickname}" already exists')
		self.cursor().execute(
			'INSERT INTO user_info (nicknames, created_on, extension_data) '
			'VALUES (?, ?, ?)',
			# TODO: generate default extension data instead of an empty dict
			(json.dumps(nicknames), utils.utc_timestamp(), json.dumps(extension_data or {}))
		)
		return int(self.cursor().execute('SELECT last_insert_rowid()').fetchone()[0])

	def find_user(self, nickname: str) -> Optional[User]:
		"""
		Find and return a User object whose `nicknames` entry in the database matches the given nickname.
		If no user was found, None will be returned.
		"""
		c = self.cursor()
		c.execute('SELECT rowid FROM user_info WHERE nicknames LIKE ?', (f'%"{nickname}"%',))
		try:
			rowid = c.fetchone()[0]
			return User(self, rowid)
		except TypeError:
			return None

	def find_or_add_user(self, nickname, extension_data: Union[str, dict] = None):
		return self.find_user(nickname) or User(self, self.add_user([nickname], extension_data))


class User(QObject):
	"""
	Represents a single user's entry in the database.
	All information is gathered from the `user_info` table, and the following columns are expected:
		* nicknames: TEXT - JSON list of nicknames, where the first one is preferred.
		* created_on: FLOAT - POSIX timestamp of the UTC time at which this entry was created.
		* extension_data: TEXT - JSON object representing extension data. More info in `extapi.store_user_data`.
	Initialized with a DatabaseWrapper and the SQLite3 rowid. If the row doesn't exist, an error is not raised;
	if you're creating User objects manually, you probably know what you're doing. The user's existence can be
	tested with the `exists()` method.
	To get User objects by searching for a name, adding a new user, etc., use the DatabaseWrapper class.
	"""
	__cache__ = {}

	def __new__(cls, database: DatabaseWrapper, rowid):
		if (database, rowid) in cls.__cache__:
			return cls.__cache__[(database, rowid)]
		self = super().__new__(cls, database, rowid)
		cls.__cache__[(database, rowid)] = self
		self.__initialized__ = False
		return self

	def __init__(self, database: DatabaseWrapper, rowid):
		if not self.__initialized__:
			super().__init__(None)
			self.__initialized__ = True
		self.database = database
		self.rowid = rowid

	def __str__(self):
		if self.exists():
			return self.name
		return '[Non-existing User]'

	def __eq__(self, other):
		return self.rowid == other.rowid

	def exists(self):
		c = self.database.cursor()
		c.execute('SELECT rowid FROM user_info WHERE rowid = ?', (self.rowid,))
		return bool(c.fetchone())

	@property
	def name(self):
		return self.nicknames[0]

	@property
	def nicknames(self):
		c = self.database.cursor()
		c.execute('SELECT nicknames FROM user_info WHERE rowid = ?', (self.rowid,))
		return json.loads(c.fetchone()[0])

	@nicknames.setter
	def nicknames(self, value):
		self.database.cursor().execute(
			'UPDATE user_info SET nicknames = ? WHERE rowid = ?',
			(json.dumps(value), self.rowid)
		)

	@property
	def created_on(self):
		c = self.database.cursor()
		c.execute('SELECT created_on FROM user_info WHERE rowid = ?', (self.rowid,))
		return utils.timestamp_to_datetime(c.fetchone()[0])

	@created_on.setter
	def created_on(self, value: float):
		self.database.cursor().execute('UPDATE user_info SET created_on = ? WHERE rowid = ?', (value, self.rowid))

	@property
	def extension_data(self):
		c = self.database.cursor()
		c.execute('SELECT extension_data FROM user_info WHERE rowid = ?', (self.rowid,))
		return json.loads(c.fetchone()[0])

	@extension_data.setter
	def extension_data(self, value: dict):
		self.database.cursor().execute(
			'UPDATE user_info SET extension_data = ? WHERE rowid = ?',
			(json.dumps(value), self.rowid)
		)


class Message(QObject):
	"""
	Represents a single message.
	A message with `None` as the source can be useful for debugging if the bot doesn't need to send a response.
	"""
	def __init__(self, source: Optional[Chat], author: User, content, timestamp=None):
		super().__init__(None)
		self.source = source
		self.author = author
		self.content = content
		self.timestamp = timestamp or datetime.datetime.now().timestamp()

	def __str__(self):
		return self.content

	async def respond(self, *args, **kwargs):
		await self.source.send(*args, **kwargs)


class Chat(QObject):
	"""
	Represents an API which can produce Message objects and to which content can be sent.
	Whenever a new message is received, `new_message()` should be called. Signals are handled automatically.
	"""
	messageReceived = Signal(Message)

	def __init__(self):
		super().__init__(None)
		self.messages: Deque[Message] = collections.deque()

	def __str__(self):
		return 'Unknown'

	def new_message(self, message: Message):
		self.messages.append(message)
		self.messageReceived.emit(message)
		return message

	async def send(self, content):
		self.new_message(Message(self, state.state.database.self_user(), content))
		state.state.anyMessageSent.emit(content)


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
		self.main_window: gui.windows.MainWindow = main_window
		self.start_time: datetime.datetime = None
		self.extension_helper = ExtensionHelper(self)
		self.database: DatabaseWrapper = None
		self.ready.connect(self._on_ready)

	def _on_ready(self):
		self.start_time = datetime.datetime.now()

	def initialize_database(self):
		self.database = DatabaseWrapper(self.profile.db_path, self.profile.db_connection)

	@property
	def uptime(self) -> datetime.timedelta:
		return datetime.datetime.now() - self.start_time

	def find_extension_by_module(self, module) -> Extension:
		return next(ext for ext in self.extensions if ext.module is module)

	def add_chat(self, chat):
		self.chats.append(chat)
		chat.messageReceived.connect(self.anyMessageReceived)
		self.chatAdded.emit(chat)


def handle_exception(loop, context):
	if exception := context.get('exception', None):
		logger.error('Unhandled exception in event loop', exc_info=exception)
	else:
		logger.error(context['message'])


def run_default():
	"""
	Run ChattyBoi with the default configuration, loading settings from the config module,
	using qasync for the main async event loop, getting a profile from the launcher,
	and with all available GUI elements enabled.
	"""
	app = QApplication(sys.argv)
	app.setApplicationName(config.qt_app_name)
	app.setOrganizationName(config.qt_org_name)
	loop = qasync.QEventLoop(app)
	loop.set_exception_handler(handle_exception)
	asyncio.set_event_loop(loop)

	def profile_select_callback(path):
		profile = profiles.Profile(path)
		_state = state.state = ApplicationState(logger, profile)
		profile.initialize()
		_state.cleanup.connect(profile.cleanup)
		_state.extension_helper.load_all()
		_state.initialize_database()
		_state.main_window = gui.MainWindow(_state)
		_state.ready.emit()
		_state.main_window.show()

	# TODO: get search paths from QSettings
	profile_dialog = gui.ProfileSelectDialog(['./profiles'])
	profile_dialog.accepted.connect(lambda: profile_select_callback(profile_dialog.get_selected_path()))
	profile_dialog.rejected.connect(QApplication.instance().quit)
	profile_dialog.show()

	with loop:
		return loop.run_forever()
