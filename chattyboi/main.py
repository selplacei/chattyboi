# SPDX-License-Identifier: Apache-2.0
import asyncio
import sys

from PySide2.QtWidgets import QApplication
import qasync

import utils, state, config, profiles, gui, chattyboi, extapi


if __name__ == '__main__':
	app = QApplication(sys.argv)
	config.load()

	loop = qasync.QEventLoop(app)
	asyncio.set_event_loop(loop)

	with loop:
		sys.exit(chattyboi.run_default())
