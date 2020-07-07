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


class Database(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state
		self.databaseEditor = DatabaseEditor(state)
		self.setLayout(QHBoxLayout())
		self.layout().addWidget(self.databaseEditor)


class Extensions(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state
		self.extension_list = ExtensionList(state, initialize=False)
		self.extension_viewer = ExtensionViewer(state)

		root_layout = QHBoxLayout()
		root_layout.addWidget(self.extension_list)
		root_layout.addWidget(self.extension_viewer)
		root_layout.setStretch(0, 1)
		root_layout.setStretch(1, 1)
		self.extension_list.itemClicked.connect(
			lambda item: self.extension_viewer.show_extension(
				next(filter(lambda ext: ext.name == item.text(), state.extensions))
			)
		)
		self.setLayout(root_layout)

		state.ready.connect(self.extension_list.initialize)


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
		self.setBackgroundRole(QPalette.Window)
		self.rootLayout = QVBoxLayout()
		self.rootLayout.addWidget(self.topLabel)
		self.rootLayout.addWidget(self.centralLabel)
		self.rootLayout.addWidget(self.aboutQtButton)
		self.rootLayout.setStretch(1, 3)
		self.setLayout(self.rootLayout)
