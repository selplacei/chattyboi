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
import sys
import sqlite3
from typing import List, Dict, Union, Tuple, Deque, Optional

import qasync
import toml
from PySide2.QtCore import Signal, QObject, QSettings
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
	This only represents the info about an extension; its module is imported separately,
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
	licence: str
	summary: str
	description: str
	requires: List[str]
	implements: List[str]

	def __init__(self, metadata, module):
		self.__dict__.update(metadata)
		self.module = module
		self._aliases = set()

	def __eq__(self, other):
		return self.module is other.module

	def __getitem__(self, item):
		if item in self.module.__all__:
			return getattr(self.module, item)

	@property
	def aliases(self):
		return {self.source, self.module.__name__, *self.implements} | self._aliases

	def add_alias(self, alias):
		self._aliases.add(alias)


class ExtensionHelper:
	"""
	Helper class for managing extensions associated with a specific state.
	To retrieve the list of needed extensions, the state's profile is used.
	When extensions are loaded, the `extensions` list of the state is updated.

	The responsibilities of this class are as follows:
		* finding extension packages from a profile's properties;
		* parsing extension metadata;
		* building the extensions' dependency tree;
		* creating and loading extension modules;
		* initializing associated Extension objects;
		* updating the state's extension list.
	"""
	@staticmethod
	def get_metadata(fp: pathlib.Path, set_defaults=True):
		metadata = {
			'author': 'Unknown',
			'version': '<unknown>',
			'license': 'No license',
			'summary': 'No summary provided.',
			'description': 'No description provided.',
			'requires': [],
			'implements': []
		} if set_defaults else {}
		metadata.update(toml.load(fp))
		if not ({'name', 'source'} <= set(metadata.keys())):
			raise ValueError(f'Extension metadata at {fp} does not provide a name and a source')
		return metadata

	@staticmethod
	def get_hash(source):
		return hashlib.md5(bytes(source, "utf-8")).hexdigest()

	@staticmethod
	def load_order(extensions: List[Tuple[pathlib.Path, dict]]) -> List[pathlib.Path]:
		"""
		Use Kahn's topological sort algorithm to find an extension load order that satisfies all dependencies.
		This function assumes no duplicate implementations. A ValueError will be raised if there is a dependency cycle.
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
			raise ValueError(
				f'Encountered a dependency cycle when finding the load order for extensions. '
				f'Remaining values in the dependency graph:\n{graph}'
			)
		return order

	def __init__(self, state):
		self.state = state

	def load(self, path, metadata, module_name=None):
		module_name = module_name or 'extension_' + self.get_hash(metadata['source'])
		spec = importlib.util.spec_from_file_location(module_name, path / '__init__.py')
		module = importlib.util.module_from_spec(spec)
		sys.modules[module_name] = module
		extension = Extension(metadata, module)
		self.state.extensions.append(extension)
		spec.loader.exec_module(module)

	def load_all(self):
		# TODO: use a config variable instead of a hardcoded extension directory
		paths = list((pathlib.Path('./extensions') / name) for name in self.state.profile.extensions)
		metadata = [self.get_metadata(fp / 'extension.toml') for fp in paths]
		# Check for duplicate implementations
		implementations = {md['source']: {md['source']} | set(md['implements']) for md in metadata}
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
	The associated connection and cursor are stored in the `connection` and `cursor()` attributes.
	"""
	SELF_NICKNAME = 'self'
	cache = {}

	def __init__(self, source: pathlib.Path, connection: sqlite3.Connection):
		self.source = source
		self.connection = connection
		DatabaseWrapper.cache[source] = self

	def __eq__(self, other):
		return self.source == other.source

	def cursor(self):
		return self.connection.cursor()

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
		# self.cursor().execute('SELECT rowid FROM user_info WHERE nicknames LIKE ?', (f'"%self\n%"',))
		# print(self.cursor().fetchall())
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
	A class that represents a single user's entry in the database.
	All information is gathered from the `user_info` table, and the following columns are expected:
		* nicknames: TEXT - newline-separated (\n) list of unique names that refer to this user,
							where the first one is the preferred/default.
		* created_on: FLOAT - POSIX timestamp of the UTC time at which this entry was created.
		* extension_data: TEXT - JSON object representing extension data. More info in `extapi.store_user_data`.
	Initialized with a DatabaseWrapper and the SQLite3 rowid. If the row doesn't exist, an error is not raised;
	if you're creating User objects manually, you probably know what you're doing. The user's existence can be
	tested with the `exists()` method.
	To get User objects by searching for a name, adding a new user, etc., use the DatabaseWrapper class.
	"""
	def __init__(self, database: DatabaseWrapper, rowid):
		super().__init__(None)
		self.database = database
		self.rowid = rowid

	def __str__(self):
		if self.exists():
			return self.name
		return '[Non-existing User]'

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
	A class representing a single message.
	Upon creation, if a source is specified, the message will be added to the message cache
	and the `messageReceived` signal will be emitted.
	A message with `None` as the source can be useful for testing, where the bot only needs
	to react to a message without interacting with its author.
	"""
	def __init__(self, source: Optional[Chat], author: User, content, timestamp=None):
		super().__init__(None)
		self.source = source
		self.author = author
		self.content = content
		self.timestamp = timestamp or datetime.datetime.now().timestamp()

	def __str__(self):
		return self.content


class Chat(QObject):
	messageReceived = Signal(Message)

	def __init__(self):
		super().__init__(None)
		self.messages: Deque[Message] = collections.deque()

	def __str__(self):
		return 'Unknown'

	def new_message(self, author, content):
		message = Message(self, author, content)
		self.messages.append(message)
		self.messageReceived.emit(message)
		return message

	async def send(self, content):
		state.state.anyMessageSent.emit(content)


class ApplicationState(QObject):
	"""
	Data structure that describes a state of the ChattyBoi application.
	The following information can be retrieved using this class:
		* the associated profile;
		* properties, i.e. system and user scope QSettings;
		* currently loaded extensions;
		* associated ExtensionHelper;
		* associated DatabaseWrapper;
		* active chat streams;
		* the main window.
	"""
	ready = Signal()
	chatAdded = Signal(Chat)
	anyMessageReceived = Signal(Message)
	anyMessageSent = Signal(str)

	@classmethod
	def default(cls):
		return cls(
			properties={'system': config.system_settings, 'user': config.user_settings},
			logger=logger
		)

	def __init__(self, properties, logger, profile=None, extensions=None, chats=None, main_window=None):
		super().__init__(None)
		self._profile = profile
		self.properties: Dict[str, QSettings] = properties
		self.logger: logging.Logger = logger
		self.extensions: List[Extension] = extensions or []
		self.chats: List[Chat] = chats or []
		self.main_window: gui.windows.MainWindow = main_window
		self.start_time: datetime.datetime = None
		self.extension_helper = ExtensionHelper(self)
		self.ready.connect(self._on_ready)

	@property
	def profile(self) -> profiles.Profile:
		return self._profile

	@profile.setter
	def profile(self, value):
		if self._profile is None:
			self._profile = value
		else:
			raise AttributeError('The profile cannot be changed after it has been set.')

	@property
	def database(self) -> DatabaseWrapper:
		return self.profile.get_database_wrapper()

	def _on_ready(self):
		self.start_time = datetime.datetime.now()

	@property
	def uptime(self) -> datetime.timedelta:
		return datetime.datetime.now() - self.start_time

	def find_extension_by_module(self, module) -> Extension:
		return next(ext for ext in self.extensions if ext.module is module)

	def add_chat(self, chat):
		self.chats.append(chat)
		chat.messageReceived.connect(self.anyMessageReceived)
		self.chatAdded.emit(chat)


delayed_connect_slots = {
	'on_ready': [],
	'always_run': [],
	'on_message': [],
	'on_cleanup': []
}


def handle_exception(loop, context):
	if exception := context.get('exception', None):
		logger.error('Unhandled exception in event loop', exc_info=exception)
	else:
		logger.error(context['message'])


def run_default():
	app = QApplication(sys.argv)
	app.setApplicationName(config.qt_app_name)
	app.setOrganizationName(config.qt_org_name)
	loop = qasync.QEventLoop(app)
	asyncio.set_event_loop(loop)
	loop.set_exception_handler(handle_exception)

	_state = state.state = ApplicationState.default()

	def profile_select_callback(path):
		profile = profiles.Profile(path)
		profile.initialize()
		state.state.profile = profile
		_state.extension_helper.load_all()
		for slot in delayed_connect_slots['on_ready']:
			_state.ready.connect(slot)
		for slot in [profile.cleanup] + delayed_connect_slots['on_cleanup']:
			app.aboutToQuit.connect(slot)

		_state.main_window = gui.MainWindow(_state)
		for slot in delayed_connect_slots['on_message']:
			_state.anyMessageReceived.connect(slot)
		_state.ready.emit()
		for coro, interval in delayed_connect_slots['always_run']:
			async def repeat():
				while loop.is_running():
					await coro()
					await asyncio.sleep(interval)
			loop.create_task(repeat())
		_state.main_window.show()

	# TODO: get search paths from QSettings
	profile_dialog = gui.ProfileSelectDialog(['./profiles'])
	profile_dialog.accepted.connect(lambda: profile_select_callback(profile_dialog.get_selected_path()))
	profile_dialog.rejected.connect(QApplication.instance().quit)
	profile_dialog.show()

	with loop:
		return loop.run_forever()
