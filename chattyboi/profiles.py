# SPDX-License-Identifier: Apache-2.0
import json
import pathlib
import sqlite3

import utils


class Profile:
	"""
	A class representing data associated with a profile.
	In ChattyBoi, a profile is essentially all information that gets loaded at runtime, except global configuration.
	In other words, a profile is an instance of what ChattyBoi stores on the disk, including:
		* the list of extensions used;
		* a user database;
		* per-profile extension data.
	Physically, a profile can be any directory that contains a valid JSON file whose name matches `PROPERTIES_FILENAME`.
	The following paths are stored:
		* PROPERTIES_FILENAME - JSON file with data used by ChattyBoi's core, including the extension list and metadata;
		* DATABASE_FILENAME - SQLite3 user database; see `Profile.initialize()` for a template;
		* EXTENSION_DATA_DIRECTORY - parent directory for storing per-profile extension data.
	"""
	PROPERTIES_FILENAME = 'profile.json'
	DATABASE_FILENAME = 'users.db'
	EXTENSION_DATA_DIRECTORY = 'extension_data'
	DEFAULT_PROPERTIES = {
		'name': 'Unnamed',
		'created_on': utils.utc_timestamp(),
		'extensions': set(),
		'note': None
	}

	def __init__(self, path: pathlib.Path):
		self.path = path
		self.properties: dict = None
		self.connection: sqlite3.Connection = None
		self.database_path = self.path / self.DATABASE_FILENAME
		self.extension_data_path = pathlib.Path(self.path / self.EXTENSION_DATA_DIRECTORY)
		self.load_properties()

	def initialize(self):
		if not self.extension_data_path.is_dir():
			self.extension_data_path.mkdir(parents=True)
		self.connection = sqlite3.connect(str(self.path / self.DATABASE_FILENAME))
		with open(pathlib.Path(__file__).parent / 'schema.sql') as schema:
			self.connection.cursor().executescript(schema.read())

	def cleanup(self):
		self.connection.commit()
		self.connection.close()
		self.save_properties()

	def get_database_wrapper(self):
		from chattyboi import DatabaseWrapper
		return DatabaseWrapper.cache.get(self.database_path) or DatabaseWrapper(self.database_path, self.connection)

	def load_properties(self):
		try:
			self.properties = json.load((self.path / self.PROPERTIES_FILENAME).open())
			self.properties['extensions'] = set(self.properties['extensions'])
		except FileNotFoundError:
			self.properties = self.DEFAULT_PROPERTIES
			self.save_properties()

	def save_properties(self):
		_properties = self.properties.copy()
		_properties['extensions'] = list(_properties['extensions'])
		json.dump(_properties, (self.path / self.PROPERTIES_FILENAME).open('w'))

	@property
	def name(self):
		return self.properties['name']

	@name.setter
	def name(self, value):
		self.properties['name'] = value

	@property
	def created_on(self):
		return utils.timestamp_to_datetime(self.properties['created_on'])

	@property
	def extensions(self):
		return self.properties['extensions']

	@extensions.setter
	def extensions(self, value):
		self.properties['extensions'] = set(value)

	@property
	def note(self):
		return self.properties['note'] or ''

	@note.setter
	def note(self, value):
		self.properties['note'] = value
