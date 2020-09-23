# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
from typing import List

import state


class Extension:
	"""
	Information about a specific loaded extension.
	This only represents the info about it; its module is imported separately,
	and destroying this object will not unload the extension.
	All attributes in the module's __all__ can be accessed through this object.
	If any of them collide with the attributes defined here, the former takes priority,
	but this behavior is strongly discouraged unless you intend to override the behavior.
	"""
	name: str
	source: str
	author: str
	version: str
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
	
	def __str__(self):
		return self.name
	
	def __eq__(self, other):
		return self.module is other.module
	
	def __hash__(self):
		return self.hash
	
	def __getattribute__(self, item):
		try:
			module = super().__getattribute__('module')
			if item in module.__all__:
				return getattr(module, item)
		except AttributeError:
			pass
		return super().__getattribute__(item)
	
	@property
	def aliases(self):
		return {self.name, self.source, self.module.__name__, *self.implements} | self._aliases
	
	def add_alias(self, alias):
		self._aliases.add(alias)
	
	@property
	def storage_path(self):
		path = state.state.profile.extension_storage_path / self.hash
		if not path.exists():
			path.mkdir(parents=True)
			logger.log(logging.INFO, f'Created extension storage directory "{path}" for "{self}"')
		return path
