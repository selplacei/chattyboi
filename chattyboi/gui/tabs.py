from PySide2.QtWidgets import QWidget, QSplitter, QBoxLayout

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
		splitter.setCollapsible(1, False)
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
