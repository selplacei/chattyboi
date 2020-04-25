# SPDX-License-Identifier: Apache-2.0
import asyncio
import sys

from PySide2.QtWidgets import QApplication
import qasync

import utils, config, profiles, gui, chattyboi, extapi

state = None

if __name__ == '__main__':
	app = QApplication(sys.argv)
	config.load()

	loop = qasync.QEventLoop(app)
	asyncio.set_event_loop(loop)

	state = chattyboi.ApplicationState.default()
	with loop:
		sys.exit(chattyboi.run_default())
