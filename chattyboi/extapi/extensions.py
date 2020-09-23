import inspect
from typing import Optional

from .types import Extension
from ._state import state

__all__ = ('get', 'this')


def get(identifier: str) -> Optional[Extension]:
	"""
	Get an Extension object that is loaded into the state and matches the identifier. It's highly encouraged to
	hardcode only the same identifiers as those used in the ``manifest.toml``'s ``requires`` field.

	:param identifier: a source, name, alias, or module name
	:return: Extension object if found, None otherwise
	"""
	return next((ext for ext in state().extensions if identifier in ext.aliases), None)


def this() -> Extension:
	"""
	Get the extension from which this function was called.

	This should only be called from within extension code, i.e. where __name__ until the first dot is guaranteed to be
	the same as in the extension's __init__.py. Use this sparingly, preferably only in simple extensions, and directly
	from extension code. This assumes that __name__ wasn't overwritten.

	:return: Extension object if found, raising a RuntimeError otherwise
	:raise: RuntimeError if not found
	"""
	if e := get(inspect.currentframe().f_back.f_globals['__name__'].split('.', 1)[0]):
		return e
	raise RuntimeError('this() must be called directly from within an extension (__init__.py or any submodule)')