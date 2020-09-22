# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import logging
import sys

import qasync
from PySide2.QtWidgets import QApplication

import config
import gui
import profiles
import state

from .extension import Extension
from .extension_helper import ExtensionHelper
from .user import User
from .database_wrapper import DatabaseWrapper
from .message import MessageContent, Message
from .chat import Chat
from .application_state import ApplicationState

logging.basicConfig(
	format=config.LOG_FORMAT,
	datefmt=config.LOG_DATEFMT,
	level=config.LOG_LEVEL
)
logger = logging.getLogger('chattyboi')


def handle_exception(loop, context):
	if exception := context.get('exception', None):
		logger.error('Unhandled exception in event loop', exc_info=exception)
	else:
		logger.error(context['message'])


def run_default():
	"""
	Run ChattyBoi with the default configuration, loading settings from the config module,
	using qasync for the main async event loop, getting a profile from the launcher,
	and with all available GUI elements enabled.
	"""
	app = QApplication(sys.argv)
	app.setApplicationName(config.QT_APP_NAME)
	app.setOrganizationName(config.QT_ORG_NAME)
	loop = qasync.QEventLoop(app)
	loop.set_exception_handler(handle_exception)
	asyncio.set_event_loop(loop)
	
	def profile_select_callback(path):
		profile = profiles.Profile(path)
		_state = state.state = ApplicationState(logger, profile)
		profile.initialize()
		_state.cleanup.connect(profile.cleanup)
		_state.extension_helper.load_all()
		_state.main_window = gui.MainWindow(_state)
		_state.ready.emit()
		_state.main_window.show()
	
	# TODO: get search paths from QSettings
	profile_dialog = gui.ProfileSelectDialog(['./profiles'])
	profile_dialog.accepted.connect(lambda: profile_select_callback(profile_dialog.get_selected_path()))
	profile_dialog.rejected.connect(QApplication.instance().quit)
	profile_dialog.show()
	
	with loop:
		return loop.run_forever()
