import asyncio
import datetime
import logging


from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import (
	QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPlainTextEdit, QLineEdit,
	QSizePolicy, QComboBox, QPushButton, QLabel, QStackedWidget
)

import config


class DashboardTab(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.chatView = DashboardChatView(state)
		self.messageSender = DashboardMessageSender(state)
		self.statusWidget = DashboardStatusWidget(state)
		self.shortcutWidget = DashboardShortcutWidget(state)
		self.customWidgetManager = DashboardCustomWidgetManager(state)

		rootLayout = QHBoxLayout()
		self.leftWidget = QWidget()
		self.rightWidget = QWidget()
		self.leftWidget.setLayout(QVBoxLayout())
		self.rightWidget.setLayout(QVBoxLayout())
		self.leftWidget.layout().addWidget(self.chatView)
		self.leftWidget.layout().addWidget(self.messageSender)
		self.rightWidget.layout().addWidget(self.customWidgetManager)
		self.rightWidget.layout().addWidget(self.shortcutWidget)
		self.customWidgetManager.add_widget('Status', self.statusWidget)
		rootLayout.addWidget(self.leftWidget)
		rootLayout.addWidget(self.rightWidget)

		self.setLayout(rootLayout)

	def addCustomWidget(self, title, widget: QWidget):
		self.customWidgetManager.add_widget(title, widget)


class DashboardChatView(QTableWidget):
	def __init__(self, state, parent=None):
		super().__init__(0, 4, parent)
		self.horizontalHeader().hide()
		self.verticalHeader().hide()
		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.resizeColumnsToContents()
		state.anyMessageReceived.connect(self.add_message)

	def resizeEvent(self, event):
		# Set the width of the last section to fill the available space, unless that is smaller than its contents,
		# in which case the section will be as wide as needed to display everything.
		# https://stackoverflow.com/a/47834343/4434353
		self.resizeColumnsToContents()
		self.resizeRowsToContents()
		self.horizontalHeader().resizeSection(3, max(
			self.sizeHintForColumn(3),
			self.viewport().size().width() - sum(self.horizontalHeader().sectionSize(i) for i in range(3))
		))

	def add_message(self, message):
		index = self.rowCount()
		self.insertRow(index)
		self.setItem(index, 0, QTableWidgetItem(datetime.datetime.fromtimestamp(message.timestamp).strftime('%H:%M')))
		self.setItem(index, 1, QTableWidgetItem(str(message.source)))
		self.setItem(index, 2, QTableWidgetItem(str(message.author)))
		self.setItem(index, 3, QTableWidgetItem(str(message.content)))
		for i in range(4):
			self.item(0, i).setFlags(~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
		self.resizeEvent(None)


class DashboardMessageSender(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state
		self.comboBox = QComboBox()
		self.lineEdit = QLineEdit()

		self.state.chatAdded.connect(self.update_chat_list)
		self.lineEdit.editingFinished.connect(self.send)
		layout = QHBoxLayout()
		layout.setContentsMargins(0, layout.contentsMargins().top(), 0, layout.contentsMargins().bottom())
		layout.addWidget(self.comboBox)
		layout.addWidget(self.lineEdit)
		self.setLayout(layout)

	def update_chat_list(self):
		self.comboBox.model().clear()
		self.comboBox.addItems(str(chat) for chat in self.state.chats)

	def selected_chat(self):
		return self.state.chats[self.comboBox.currentIndex()]

	def send(self):
		if content := self.lineEdit.text():
			asyncio.get_event_loop().create_task(self.selected_chat().send(content))
			self.lineEdit.setText('')


class DashboardCustomWidgetManager(QWidget):
	def __init__(self, status, parent=None):
		super().__init__(parent)
		self.status = status
		self.stackedWidget = QStackedWidget()
		self.pageSwitcher = QWidget()
		self.leftButton = QPushButton('<-')
		self.rightButton = QPushButton('->')
		self.comboBox = QComboBox()

		rootLayout = QVBoxLayout()
		switcherLayout = QHBoxLayout()
		switcherLayout.addWidget(self.leftButton)
		switcherLayout.addWidget(self.comboBox)
		switcherLayout.addWidget(self.rightButton)
		self.pageSwitcher.setLayout(switcherLayout)
		rootLayout.addWidget(self.stackedWidget)
		rootLayout.addWidget(self.pageSwitcher)
		switcherLayout.setMargin(0)
		rootLayout.setMargin(0)
		self.setLayout(rootLayout)

		self.comboBox.currentIndexChanged.connect(self.stackedWidget.setCurrentIndex)
		self.comboBox.currentIndexChanged.connect(self.update_buttons)
		self.leftButton.clicked.connect(self.go_left)
		self.rightButton.clicked.connect(self.go_right)
		self.update_buttons()

	def add_widget(self, title, widget):
		self.stackedWidget.addWidget(widget)
		self.comboBox.addItem(title)
		self.update_buttons()

	def currentWidget(self):
		return self.stackedWidget.currentWidget()

	def update_buttons(self):
		index = self.stackedWidget.currentIndex()
		self.leftButton.setEnabled(index > 0)
		self.rightButton.setEnabled(index < self.stackedWidget.count() - 1)

	def go_left(self):
		index = self.stackedWidget.currentIndex()
		if index > 0:
			self.stackedWidget.setCurrentIndex(index - 1)
		self.update_buttons()

	def go_right(self):
		index = self.stackedWidget.currentIndex()
		if index < self.stackedWidget.count() - 1:
			self.stackedWidget.setCurrentIndex(index + 1)
		self.update_buttons()


class DashboardStatusWidget(QWidget):
	class Handler(logging.Handler):
		def __init__(self, widget):
			super().__init__()
			self.widget = widget
			self.records = []
			self.setFormatter(
				logging.Formatter(config.log_format.replace('%(name)s:', ''), datefmt=config.log_datefmt)
			)

		def emit(self, record):
			self.records.append(record)
			if self.widget.record_should_be_displayed(record):
				self.widget.add_message(self.format(record))

	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state
		self.log_level_indices = {logging.DEBUG: 0, logging.INFO: 1, logging.WARNING: 2}
		self._records = []
		self.handler = DashboardStatusWidget.Handler(self)
		self.state.logger.addHandler(self.handler)

		self.plainTextEdit = QPlainTextEdit()
		self.leftLabel = QLabel('Show:')
		self.logLevelSelector = QComboBox()
		self.statusLabel = QLabel()
		self.statusTimer = QTimer()

		root_layout = QVBoxLayout()
		top_layout = QHBoxLayout()
		top_layout.addWidget(self.leftLabel)
		top_layout.addWidget(self.logLevelSelector)
		top_layout.addWidget(self.statusLabel)
		top_layout.setMargin(0)
		top_widget = QWidget()
		top_widget.setLayout(top_layout)
		root_layout.addWidget(top_widget)
		root_layout.addWidget(self.plainTextEdit)
		root_layout.setMargin(0)

		self.setLayout(root_layout)
		self.statusTimer.timeout.connect(self.update_status)
		self.statusTimer.start(1000)
		self.leftLabel.setFixedWidth(self.leftLabel.sizeHint().width())
		self.logLevelSelector.addItems(['Debug', 'Info', 'Warnings'])
		self.logLevelSelector.setCurrentIndex(self.log_level_indices.get(self.state.logger.getEffectiveLevel(), 2))
		self.logLevelSelector.currentIndexChanged.connect(self.update_log_level)
		self.state.ready.connect(self.update_status)

	def record_should_be_displayed(self, record):
		return self.log_level_indices[record.levelno] >= self.logLevelSelector.currentIndex()

	def update_log_level(self):
		self.plainTextEdit.setPlainText('\n'.join(
			self.handler.format(record) for record in self.handler.records if self.record_should_be_displayed(record)
		))

	def update_status(self):
		uptime_seconds = self.state.uptime.seconds
		uptime_text = 'Uptime: '
		if uptime_seconds >= 86400:
			uptime_text += f'{round(uptime_seconds / 86400)} days'
		elif uptime_seconds >= 3600:
			hours, remainder = divmod(uptime_seconds, 3600)
			uptime_text += f'{hours}h {remainder / 60}m'
		else:
			minutes, remainder = divmod(uptime_seconds, 60)
			uptime_text += f'{minutes}m {round(remainder)}s'
		self.statusLabel.setText(
			f'Extensions: {len(self.state.extensions)} | {uptime_text}'
		)

	def add_message(self, text):
		self.plainTextEdit.appendPlainText(text)
		self.plainTextEdit.verticalScrollBar().setValue(self.plainTextEdit.verticalScrollBar().maximum())


class DashboardShortcutWidget(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state
		layout = QHBoxLayout()
		layout.addWidget(QPushButton('Shortcut 1'))
		layout.addWidget(QPushButton('Shortcut 2'))
		layout.setMargin(0)
		self.setLayout(layout)
