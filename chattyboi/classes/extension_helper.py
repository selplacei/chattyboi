# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import pathlib
import sys

import toml

import config
from . import Extension


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
	@dataclasses.dataclass
	class _UninitializedExtensionInfo:
		path: str
		metadata: dict
		requires: set
		implements: set
	
	@staticmethod
	def get_metadata(fp: pathlib.Path, use_defaults=True):
		metadata = {
			'author': 'Unknown',
			'version': '<unknown>',
			'license': 'No license',
			'summary': 'No summary provided.',
			'description': 'No description provided.',
			'requires': [],
			'supports': [],
			'implements': []
		} if use_defaults else {}
		metadata.update(toml.load(fp))
		if 'name' not in metadata or 'source' not in metadata:
			raise RuntimeError(f'Extension metadata at {fp} does not provide a name and a source')
		return metadata
	
	@staticmethod
	def get_hash(source):
		return hashlib.md5(bytes(source, "utf-8")).hexdigest()
	
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
		"""
		:raise RuntimeError: if any error is encountered, specifically: duplicate implementations if disallowed,
			missing dependencies, and dependency cycles.
		"""
		extension_root = pathlib.Path(config.user_settings.get('extension root', './extensions'))
		extension_info = [self._UninitializedExtensionInfo(
			str(path), self.get_metadata(path), set(), set()
		) for path in map(lambda name: extension_root / name, self.state.profile.paths)]
		implemented = set()
		
		# Populate extension info with what can be known immediately
		for e in extension_info:
			e.implements.add(e.metadata['name'])
			e.implements.add(e.metadata['source'])
			e.implements |= set(e.metadata['implements'])
			if conflict := (e.implements & implemented):
				# TODO: add a config variable to allow duplicate implementations
				# In that case, treat all duplicates as dependencies.
				other = next(o.metadata["name"] for o in extension_info if set(o.implements) & implemented)
				raise RuntimeError(
					f'Duplicate extension implementations found:\n'
					f'\"{e.metadata["name"]}\" ({e.path})\n'
					f'implements {conflict}, which is already satisfied by\n'
					f'\"{other.metadata["name"]} ({other.path})\"\n'
				)
			implemented |= e.implements
			e.requires += e.metadata['requires']
			
		# Check that hard dependencies are satisfied and add optional ones
		for e in extension_info:
			if not (e.requires.issubset(implemented)):
				raise RuntimeError(
					f'Extension dependencies not satisfied:\n'
					f'\"{e.metadata["name"]}\" ({e.path})\n'
					f'requires implementations of the following:\n' +
					'\n'.join(e.requires.difference(implemented))
				)
			for other in e.metadata['supports']:
				if other in implemented:
					e.requires += other
		
		# Use Kahn's topological sort algorithm to find the extension load order
		ordered = []
		graph = {e: [] for e in extension_info}
		for u in extension_info:
			for v in filter(lambda o: o is not u, extension_info):
				if v.implements & u.requires:
					graph[u] = v
		queue = [u for u, v in graph.items() if len(v) == 0]
		while queue:
			n = queue.pop()
			ordered.append(n)
			for m in (node for node, edges in graph.items() if n in edges):
				graph[m].remove(n)
				if len(graph[m]) == 0:
					queue.append(m)
		if any(edges for node, edges in graph.items()):
			raise RuntimeError(
				f'Encountered a dependency cycle when finding the load order. '
				f'These extensions probably caused this error:\n' +
				'\n'.join(f'\"{e.metadata["name"]}\" ({e.path})' for e in graph)
			)
		
		# Load extensions in order
		for e in ordered:
			self.load(e.path, e.metadata)
