# SPDX-License-Identifier: Apache-2.0
import asyncio
import hashlib
import importlib.util
import pathlib

import qasync
from PySide2.QtCore import Signal, QObject
from PySide2.QtWidgets import QApplication

import main
import config
import gui
import profiles


def run_default():
	def profile_select_callback(path):
		profile = profiles.Profile(path)
		main.state.profile = profile
		profile.initialize()
		main.state.extension_helper.find_and_load_all()

	profile_dialog = gui.ProfileSelectDialog()
	profile_dialog.accepted.connect(lambda: profile_select_callback(profile_dialog.get_selected_profile_path()))
	profile_dialog.rejected.connect(QApplication.instance().quit)
	profile_dialog.show()

	return asyncio.get_event_loop().run_forever()


def load_extension(path, to_state, module_name=None):
	pass


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
	The state of the currently running application can be retrieved via `main.state`.
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
	When extensions are loaded, the `extensions` attribute of the state is updated by this object.

	The responsibilities of this class are as follows:
		* finding extension packages from a profile's properties;
		* parsing extension metadata;
		* building the extensions' dependency tree;
		* creating and loading extension modules;
		* initializing associated Extension objects;
		* updating the state's extension list.
	"""
	def __init__(self, state):
		self.state = state

	def extension_paths(self):
		for path in self.state.profile.properties['extensions']:
			yield pathlib.Path(path)

