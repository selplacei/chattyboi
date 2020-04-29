import typing

import chattyboi
from state import state


def add_extension_alias(source, name):
	extension = get_extension(source)
	if extension is None:
		raise ValueError(f'The extension [{source}] does not exist')
	if (test_duplicate := get_extension(name)) and test_duplicate != extension:
		raise ValueError(f'An extension with the name or alias {name} already exists')
	extension.aliases.add(name)


def get_extension(identifier: str) -> typing.Optional[chattyboi.Extension]:
	"""
	Get an Extension object that matches the identifier and is loaded into the state.
	Useful for retrieving the current extension, i.e. `get_extension(__name__)`.

	:param identifier: a source, a name, an alias, or a module name
	:return: chattyboi.Extension object if found, None otherwise.
	"""
	return next((candidate for candidate in state.extensions if identifier in candidate.aliases), None)
