# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json

from PySide2.QtCore import QObject

import chattyboi
import utils


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
	
	def __new__(cls, database: chattyboi.DatabaseWrapper, rowid):
		if (database, rowid) in cls.__cache__:
			return cls.__cache__[(database, rowid)]
		self = super().__new__(cls, database, rowid)
		cls.__cache__[(database, rowid)] = self
		self.__initialized__ = False
		return self
	
	def __init__(self, database: chattyboi.DatabaseWrapper, rowid):
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
		return self.exists() and self.rowid == other.rowid
	
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
	
	def get_data(self, extension):
		return self.extension_data.get(extension.hash, {})
	
	def store_data(self, extension, data):
		all_data = self.extension_data
		all_data[extension.hash] = data
		self.extension_data = all_data
