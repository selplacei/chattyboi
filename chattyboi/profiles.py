# SPDX-License-Identifier: Apache-2.0
import json
import pathlib
import sqlite3

import utils


class Profile:
	PROPERTIES_FILENAME = 'profile.json'
	DATABASE_FILENAME = 'users.db'
	EXTENSION_DATA_DIRECTORY = 'extension_data'
	DEFAULT_PROPERTIES = {
		'name': 'Unnamed',
		'created_at': utils.utc_timestamp(),
		'extensions': []
	}

	def __init__(self, path: pathlib.Path):
		self.path = path
		self.properties: dict = None
		self.connection: sqlite3.Connection = None
		self.database_path = self.path / self.DATABASE_FILENAME
		self.extension_data_dir = pathlib.Path(self.path / self.EXTENSION_DATA_DIRECTORY)
		self.load_properties()

	def __enter__(self):
		self.initialize()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.connection.commit()
		self.connection.close()

	def initialize(self):
		if not self.extension_data_dir.is_dir():
			self.extension_data_dir.mkdir(parents=True)
		self.connection = sqlite3.connect(str(self.path / self.DATABASE_FILENAME))
		self.connection.cursor().execute(
			'CREATE TABLE IF NOT EXISTS user_info ('
			'username TEXT NOT NULL, '
			'created_on FLOAT, '
			'extension_data TEXT'
			')'
		)

	def get_database_wrapper(self):
		from chattyboi import DatabaseWrapper
		return DatabaseWrapper.cache.get(self.database_path) or DatabaseWrapper(self.database_path, self.connection)

	def load_properties(self):
		try:
			self.properties = json.load((self.path / self.PROPERTIES_FILENAME).open())
		except FileNotFoundError:
			self.properties = self.DEFAULT_PROPERTIES
			self.save_properties()

	def save_properties(self):
		json.dump(self.properties, (self.path / self.PROPERTIES_FILENAME).open('w'))

	@property
	def name(self):
		return self.properties['name']
