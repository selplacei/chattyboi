from PySide2.QtWidgets import QWidget

from .widgets import *


class Dashboard(QWidget):
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
