# SPDX-License-Identifier: Apache-2.0
import asyncio
import hashlib
import importlib.util
import itertools
import pathlib
import sys
from typing import List, Tuple

import qasync
from PySide2.QtCore import Signal, QObject
from PySide2.QtWidgets import QApplication
import toml

import config
import gui
import profiles
import state


def run_default():
	state.state = ApplicationState.default()

	def profile_select_callback(path):
		profile = profiles.Profile(path)
		state.state.profile = profile
		profile.initialize()
		state.state.extension_helper.load_all()

	# TODO: get search paths from QSettings
	profile_dialog = gui.ProfileSelectDialog(['./profiles'])
	profile_dialog.accepted.connect(lambda: profile_select_callback(profile_dialog.get_selected_profile_path()))
	profile_dialog.rejected.connect(QApplication.instance().quit)
	profile_dialog.show()

	return asyncio.get_event_loop().run_forever()


class ApplicationState(QObject):
	"""
	Data structure that describes a state of the ChattyBoi application.
	The following information can be retrieved using this class:
		* the associated profile;
		* properties, i.e. system and user scope QSettings;
		* currently loaded extensions;
		* associated ExtensionHelper;
		* associated DatabaseWrapper.
		* active chat streams;
	The state of the currently running application can be retrieved through the `state` module.
	"""
	@classmethod
	def default(cls):
		return cls(
			properties={'system': config.system_settings, 'user': config.user_settings}
		)

	def __init__(self, properties, profile=None, extensions=None, chats=None, database_wrapper=None):
		super().__init__(None)
		self._profile = profile
		self.database = database_wrapper
		self.properties = properties
		self.extensions = extensions or []
		self.extension_helper = ExtensionHelper(self)
		self.chats = chats or []

	@property
	def profile(self):
		return self._profile

	@profile.setter
	def profile(self, value):
		if self._profile is None:
			self._profile = value
			self.database = profiles.DatabaseWrapper(self._profile.database_connection)
		else:
			raise AttributeError('The profile cannot be changed after it has been set.')


class Extension:
	"""
	Information about a specific loaded extension.
	This only represents the data about an extension; the actual associated module is imported separately,
	and destroying this object will not unload the associated extension.

	The following information can be retrieved using this class:
		* metadata: accessed as normal attributes. See `__init__` for required keys.
		* associated module: contained in the `module` attribute.
		* public attributes of the module: accessed with `__get__`, i.e. as in a dict (extension['key']).
	"""

	def __init__(self, metadata, module):
		"""
		`metadata` should have the following keys:
			name, author, version, source, license, summary, description, requires, implements
		"""
		self.__dict__.update(metadata)
		self.module = module

	def __getitem__(self, item):
		if item in self.module.__all__:
			return getattr(self.module, item)


class ExtensionHelper:
	"""
	Helper class for managing extensions associated with a specific state.
	To retrieve the list of needed extensions, the state's profile is used.
	When extensions are loaded, the `extensions` attribute of the state is updated automatically.

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
		if not ({'name', 'source'} <= set(metadata)):
			raise ValueError(f'Extension metadata at {fp} does not provide a name and a source')
		return metadata

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
				f'Encountered a dependency cycle when finding the load order for extensions.'
				f'Remaining values in the dependency graph:\n{graph}'
			)
		return order

	def __init__(self, state):
		self.state = state

	def paths(self):
		for path in self.state.profile.properties['extensions']:
			yield pathlib.Path(path)

	def load(self, path, metadata, module_name=None):
		module_name = module_name or f'extension_{hashlib.md5(bytes(metadata["source"], "utf-8")).hexdigest()}'
		spec = importlib.util.spec_from_file_location(module_name, path / '__init__.py')
		module = importlib.util.module_from_spec(spec)
		sys.modules[module_name] = module
		extension = Extension(metadata, module)
		self.state.extensions.append(extension)
		spec.loader.exec_module(module)

	def load_all(self):
		paths = self.paths()
		metadata = [self.get_metadata(fp) for fp in paths]
		# Check for duplicate implementations
		implementations = {md['source']: {md['source']} | set(md['implements']) for md in metadata}
		for left, right in filter(lambda src: src[0] != src[1], itertools.product(implementations.keys(), repeat=2)):
			if conflicts := implementations[left] & implementations[right]:
				raise RuntimeError(
					f'Duplicate extension implementations found:'
					f'Both [{left}] and [{right}] implement {conflicts}'
				)
		for path, metadata in self.load_order(zip(paths, metadata)):
			self.load(path, metadata)
