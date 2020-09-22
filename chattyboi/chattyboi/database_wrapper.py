# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import pathlib
import sqlite3
from typing import Union, Optional

import chattyboi
import utils


class DatabaseWrapper(sqlite3.Connection):
	"""
	Wrapper around a profile's SQLite3 database that provides ChattyBoi-specific helper functions.
	"""
	SELF_NICKNAME = 'self'
	
	def __init__(self, source: pathlib.Path, *args, **kwargs):
		super().__init__(source, *args, **kwargs)
		self.source = source
	
	def __eq__(self, other):
		return self.source == other.source
	
	def __hash__(self):
		return id(self)
	
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
			(json.dumps(nicknames), utils.utc_timestamp(), json.dumps(extension_data or {}))
		)
		return int(self.cursor().execute('SELECT last_insert_rowid()').fetchone()[0])
	
	def find_user(self, nickname: str) -> Optional[chattyboi.User]:
		"""
		Find and return a User object whose `nicknames` entry in the database matches the given nickname.
		If no user was found, None will be returned.
		"""
		c = self.cursor()
		c.execute('SELECT rowid FROM user_info WHERE nicknames LIKE ?', (f'%"{nickname}"%',))
		try:
			rowid = c.fetchone()[0]
			return chattyboi.User(self, rowid)
		except TypeError:
			return None
	
	def find_or_add_user(self, nickname, extension_data: Union[str, dict] = None) -> chattyboi.User:
		return self.find_user(nickname) or chattyboi.User(self, self.add_user([nickname], extension_data))
