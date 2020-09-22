# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import pathlib
import sys
from typing import List, Tuple

import toml

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
