import logging
import chattyboi
from . import state

NOTSET = logging.NOTSET
DEBUG = logging.DEBUG
INFO = logging.INFO
WARN = logging.WARN
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


def log(level, message: str):
	"""
	Log to the chattyboi logger. If your extension runs its own processing, it may make sense to use your own logger.
	The levels are the same as in the ``logging`` module.
	"""
	chattyboi.logger.log(level, message)


def log_handler():
	"""
	:return: The global application state's logging handler (i.e. outputs to the status widget)
	"""
	# FIXME: make this handler a part of the state directly
	return state().main_window.dashboardTab.statusWidget.handler
