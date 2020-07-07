import asyncio
import datetime
import json
import logging


from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import (
	QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem, QPlainTextEdit, QLineEdit,
	QSizePolicy, QComboBox, QPushButton, QLabel, QStackedWidget, QAbstractItemView, QCheckBox, QTableView
)
from PySide2.QtGui import QTextOption, QStandardItemModel, QStandardItem

import utils


class DashboardChatView(QTableWidget):
	def __init__(self, state, parent=None):
		super().__init__(0, 4, parent)
		self.setHorizontalHeaderLabels(['Time', 'Chat', 'Author', 'Message'])
		self.verticalHeader().hide()
		self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
		self.setWordWrap(False)
		for i in range(3):
			self.horizontalHeader().resizeSection(i, self.horizontalHeader().sectionSizeHint(i) + 20)
		state.anyMessageReceived.connect(self.add_message)

	def viewportEvent(self, event):
		# Set the width of the last section to fill the available space, unless that is smaller than its contents,
		# in which case the section will be as wide as needed to display everything.
		# https://stackoverflow.com/a/47834343/4434353
		self.resizeRowsToContents()
		minimum_width = sum(self.horizontalHeader().sectionSize(i) for i in range(3))
		self.setMinimumWidth(minimum_width)
		self.horizontalHeader().resizeSection(3, max(
			self.sizeHintForColumn(3),
			self.viewport().size().width() - minimum_width)
		)
		return super().viewportEvent(event)

	def add_message(self, message):
		index = self.rowCount()
		self.insertRow(index)
		self.setItem(index, 0, QTableWidgetItem(datetime.datetime.fromtimestamp(message.timestamp).strftime('%H:%M')))
		self.setItem(index, 1, QTableWidgetItem(str(message.source)))
		self.setItem(index, 2, QTableWidgetItem(str(message.author)))
		self.setItem(index, 3, QTableWidgetItem(str(message.content)))
		for i in range(4):
			self.item(index, i).setFlags(~Qt.ItemIsEditable)
		self.resizeColumnToContents(3)
		self.updateGeometry()


class DashboardMessageSender(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state
		self.comboBox = QComboBox()
		self.lineEdit = QLineEdit()

		self.state.chatAdded.connect(self.update_chat_list)
		self.lineEdit.returnPressed.connect(self.send)
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
		self.comboBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		self.setLayout(rootLayout)

		self.comboBox.currentIndexChanged.connect(self.stackedWidget.setCurrentIndex)
		self.comboBox.currentIndexChanged.connect(self.update_buttons)
		self.leftButton.clicked.connect(self.go_left)
		self.rightButton.clicked.connect(self.go_right)
		self.update_buttons()

	def sizeHint(self):
		return self.minimumSizeHint()

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
			self.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M'))

		def emit(self, record):
			self.widget.records.append(record)
			if self.widget.should_display_record(record):
				self.widget.add_message(self.format(record))

	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state
		self.log_level_indices = {logging.DEBUG: 0, logging.INFO: 1, logging.WARNING: 2}
		self.records = []
		self.handler = DashboardStatusWidget.Handler(self)
		self.state.logger.addHandler(self.handler)

		self.plainTextEdit = QPlainTextEdit()
		self.logLevelSelector = QComboBox()
		self.checkboxContainer = QWidget()
		self.wordWrapCheckbox = QCheckBox()
		self.wordWrapLabel = QLabel('Word wrap')
		self.leftLabel = QLabel('Show:')
		self.statusLabel = QLabel()
		self.statusTimer = QTimer()

		root_layout = QVBoxLayout()
		top_layout = QHBoxLayout()
		bottom_layout = QHBoxLayout()
		top_layout.addWidget(self.leftLabel)
		top_layout.addWidget(self.logLevelSelector)
		top_layout.addWidget(self.statusLabel)
		top_layout.setMargin(0)
		bottom_layout.addWidget(self.wordWrapCheckbox)
		bottom_layout.addWidget(self.wordWrapLabel)
		bottom_layout.setMargin(0)
		top_widget = QWidget()
		top_widget.setLayout(top_layout)
		bottom_widget = QWidget()
		bottom_widget.setLayout(bottom_layout)
		root_layout.addWidget(top_widget)
		root_layout.addWidget(self.plainTextEdit)
		root_layout.addWidget(bottom_widget)
		root_layout.setMargin(0)

		self.setLayout(root_layout)
		self.statusTimer.timeout.connect(self.update_status)
		self.leftLabel.setFixedWidth(self.leftLabel.sizeHint().width())
		self.wordWrapCheckbox.setFixedWidth(self.wordWrapCheckbox.minimumSizeHint().width())
		self.logLevelSelector.addItems(['Debug', 'Info', 'Warnings'])
		self.logLevelSelector.setCurrentIndex(self.log_level_indices[logging.INFO])
		self.logLevelSelector.currentIndexChanged.connect(self.update_log_level)
		self.plainTextEdit.setReadOnly(True)
		self.plainTextEdit.setWordWrapMode(QTextOption.NoWrap)
		self.wordWrapCheckbox.stateChanged.connect(lambda s: self.plainTextEdit.setWordWrapMode(
			QTextOption.WrapAtWordBoundaryOrAnywhere if s == 2 else QTextOption.NoWrap
		))
		self.wordWrapCheckbox.stateChanged.connect(self.plainTextEdit.repaint)
		self.state.ready.connect(self.update_log_level)
		self.state.ready.connect(lambda: self.statusTimer.start(1000))
		self.state.ready.connect(self.update_status)

	def should_display_record(self, record):
		return self.log_level_indices.get(record.levelno, 3) >= self.logLevelSelector.currentIndex()

	def update_log_level(self):
		self.plainTextEdit.horizontalScrollBar().setValue(0)
		self.plainTextEdit.setPlainText('\n'.join(
			self.handler.format(record) for record in self.records if self.should_display_record(record)
		))

	def update_status(self):
		self.statusLabel.setText(self.uptime_text())

	def uptime_text(self):
		seconds = self.state.uptime.seconds
		text = 'Uptime: '
		if seconds >= 86400:
			text += f'{round(seconds / 86400)} days'
		elif seconds >= 3600:
			hours, remainder = divmod(seconds, 3600)
			text += f'{hours}h {remainder / 60}m'
		else:
			minutes, remainder = divmod(seconds, 60)
			text += f'{minutes}m {round(remainder)}s'
		return text

	def add_message(self, text):
		self.plainTextEdit.appendPlainText(text)
		self.plainTextEdit.verticalScrollBar().setValue(self.plainTextEdit.verticalScrollBar().minimum())


class DashboardShortcutWidget(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state
		layout = QHBoxLayout()
		layout.addWidget(QPushButton('Shortcut 1'))
		layout.addWidget(QPushButton('Shortcut 2'))
		layout.setMargin(0)
		self.setLayout(layout)


class DatabaseEditor(QWidget):
	COLUMNS = ['ID', 'Nicknames', 'Created on', 'Extension data']
	UPDATE_INTERVAL_MS = 4000

	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.display_limit = 100
		self.use_search_bar = False
		self.db_wrapper = state.database
		self.db_cursor = state.database.cursor()
		self.searchBar = QLineEdit()
		self.mainTableView = QTableView()
		self.mainTableModel = QStandardItemModel(0, len(self.COLUMNS))
		self.updateTimer = QTimer()

		self.mainTableModel.setHorizontalHeaderLabels(self.COLUMNS)
		self.mainTableView.horizontalHeader().setStretchLastSection(True)
		self.mainTableView.setWordWrap(False)
		self.mainTableView.verticalHeader().setVisible(False)
		self.mainTableView.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
		self.searchBar.textEdited.connect(self.onSearchBarTextEdited)
		self.updateTimer.timeout.connect(self.update_data)
		self.updateTimer.start(self.UPDATE_INTERVAL_MS)

		rootLayout = QVBoxLayout()
		topLayout = QHBoxLayout()
		topWidget = QWidget()
		topLayout.addWidget(QLabel('Search for nickname:'))
		topLayout.addWidget(self.searchBar)
		topWidget.setLayout(topLayout)
		rootLayout.addWidget(topWidget)
		rootLayout.addWidget(self.mainTableView)
		self.setLayout(rootLayout)
		self.update_data()
		self.mainTableView.resizeColumnsToContents()

	def onSearchBarTextEdited(self):
		self.use_search_bar = (len(self.searchBar.text()) > 1)
		if self.use_search_bar:
			self.updateTimer.stop()
		else:
			self.updateTimer.start(self.UPDATE_INTERVAL_MS)
		self.update_data()

	def update_data(self):
		self.mainTableModel.setRowCount(0)
		if self.use_search_bar:
			self.db_cursor.execute(
				'SELECT rowid, nicknames, created_on, extension_data '
				'FROM user_info WHERE nicknames LIKE ? ORDER BY rowid ASC',
				(f'%{self.searchBar.text()}%',)
			)
		else:
			self.db_cursor.execute(
				'SELECT rowid, nicknames, created_on, extension_data '
				'FROM user_info ORDER BY rowid ASC LIMIT ?',
				(self.display_limit,)
			)
		for row in self.db_cursor.fetchall():
			self.mainTableModel.appendRow([
				QStandardItem(str(row[0])),
				QStandardItem(str(json.loads(row[1]))),
				QStandardItem(utils.timestamp_to_datetime(row[2]).strftime('%y-%m-%d %H:%M')),
				QStandardItem(str(json.loads(row[3])))
			])
		self.mainTableView.setModel(self.mainTableModel)

