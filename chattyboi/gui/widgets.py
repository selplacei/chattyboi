import datetime


from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
	QWidget, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPlainTextEdit, QLineEdit,
	QSizePolicy
)


class DashboardTab(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.chatView = DashboardChatView(state)
		self.messageSender = DashboardMessageSender(state)
		self.logWidget = DashboardLogWidget(state)
		self.shortcutWidget = DashboardShortcutWidget(state)

		rootLayout = QHBoxLayout()
		leftWidget = QWidget()
		rightWidget = QWidget()
		leftWidget.setLayout(QVBoxLayout())
		rightWidget.setLayout(QVBoxLayout())
		leftWidget.layout().addWidget(self.chatView)
		leftWidget.layout().addWidget(self.messageSender)
		rightWidget.layout().addWidget(self.logWidget)
		rightWidget.layout().addWidget(self.shortcutWidget)
		rootLayout.addWidget(leftWidget)
		rootLayout.addWidget(rightWidget)

		self.setLayout(rootLayout)


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
		# in which case that will become the size, and a horizontal scrollbar will appear.
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
		self.resizeColumnsToContents()


class DashboardMessageSender(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state


class DashboardLogWidget(QPlainTextEdit):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state

	def add_message(self, text):
		self.appendPlainText(text)
		self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class DashboardShortcutWidget(QWidget):
	def __init__(self, state, parent=None):
		super().__init__(parent)
		self.state = state
