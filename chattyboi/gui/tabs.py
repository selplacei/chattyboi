from PySide2.QtCore import Qt
from PySide2.QtGui import QPalette
from PySide2.QtWidgets import QWidget, QSplitter, QVBoxLayout, QApplication

import main
from .widgets import *


class Dashboard(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.chatView = DashboardChatView(state)
		self.messageSender = DashboardMessageSender(state)
		self.statusWidget = DashboardStatusWidget(state)
		self.shortcutWidget = DashboardShortcutWidget(state)
		self.customWidgetManager = DashboardCustomWidgetManager(state)

		splitter = QSplitter()
		self.leftWidget = QWidget()
		self.rightWidget = QWidget()
		self.leftWidget.setLayout(QVBoxLayout())
		self.rightWidget.setLayout(QVBoxLayout())
		self.leftWidget.layout().addWidget(self.chatView)
		self.leftWidget.layout().addWidget(self.messageSender)
		self.rightWidget.layout().addWidget(self.customWidgetManager)
		self.rightWidget.layout().addWidget(self.shortcutWidget)
		self.customWidgetManager.add_widget('Status', self.statusWidget)
		splitter.addWidget(self.leftWidget)
		splitter.addWidget(self.rightWidget)
		splitter.setStretchFactor(0, 2)
		splitter.setStretchFactor(1, 1)
		self.setLayout(QVBoxLayout())
		self.layout().addWidget(splitter)

	def addCustomWidget(self, title, widget: QWidget):
		self.customWidgetManager.add_widget(title, widget)


class DatabaseViewer(QWidget):
	# https://doc.qt.io/qt-5/qsqlrelationaltablemodel.html
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state
		self.setLayout(QHBoxLayout())
		self.layout().addWidget(QLabel('TBD'))


class About(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state
		self.name = 'ChattyBoi'
		self.author = 'selplacei <ilyaviaik at gmail.com>'
		self.version = 'pre-alpha, unknown'
		self.license = ('Apache 2.0', 'https://www.apache.org/licenses/LICENSE-2.0.html')
		self.url = 'https://github.com/selplacei/chattyboi'
		self.label_text = (
			f'<b>{self.name}</b> version <code>{self.version}</code><br />'
			f'Author: {self.author}<br />'
			f'Upstream URL: <a href="{self.url}">{self.url}</a><br /><br />'
			f'{self.name} is Free Software, licensed under <a href="{self.license[1]}">{self.license[0]}</a>.<br />'
			f'You are free to distribute, modify, and use this software for any purpose under this license.<br /><br />'
			f'This project uses <a href="https://www.qt.io/qt-for-python">Qt for Python</a>, licensed under the '
			f'<a href="https://www.gnu.org/licenses/lgpl-3.0.en.html">GNU Lesser General Public License</a>.'
		)

		self.topLabel = QLabel(f'<h2>About {self.name}</h2>')
		self.centralLabel = QLabel(self.label_text)
		self.aboutQtButton = QPushButton('About Qt')
		self.topLabel.setTextFormat(Qt.RichText)
		self.centralLabel.setTextFormat(Qt.RichText)
		self.centralLabel.setWordWrap(True)
		self.centralLabel.setAlignment(Qt.AlignLeft | Qt.AlignTop)
		self.centralLabel.setOpenExternalLinks(True)
		self.aboutQtButton.setFixedWidth(self.aboutQtButton.sizeHint().width())
		self.aboutQtButton.clicked.connect(QApplication.instance().aboutQt)
		self.setAutoFillBackground(True)
		self.setBackgroundRole(QPalette.Base)
		self.rootLayout = QVBoxLayout()
		self.rootLayout.addWidget(self.topLabel)
		self.rootLayout.addWidget(self.centralLabel)
		self.rootLayout.addWidget(self.aboutQtButton)
		self.rootLayout.setStretch(1, 3)
		self.setLayout(self.rootLayout)
