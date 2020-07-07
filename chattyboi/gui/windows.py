# SPDX-License-Identifier: Apache-2.0
import pathlib
from typing import List, Union

from PySide2.QtCore import QStringListModel
from PySide2.QtWidgets import (
	QWidget, QHBoxLayout, QVBoxLayout, QMainWindow, QDialog, QListView, QPushButton, QTabWidget, QSizePolicy
)

import profiles
from . import tabs


class ProfileSelectDialog(QDialog):
	def __init__(self, search_paths: List[Union[str, pathlib.Path]], *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setLayout(QVBoxLayout())
		self.profileListView = QListView()
		self.profileListModel = QStringListModel()
		self.cancel_button = QPushButton('Cancel')
		self.confirm_button = QPushButton('Confirm')
		self.profile_paths = [
			pathlib.Path(profile)
			for parent in search_paths
			for profile in pathlib.Path(parent).glob('*')
			if (profile / 'profile.json').is_file()
		]

		self.profileListModel.setStringList([profiles.Profile(path).name for path in self.profile_paths])
		self.profileListView.setModel(self.profileListModel)
		self.profileListView.setSelectionMode(QListView.SingleSelection)
		self.layout().addWidget(self.profileListView)
		self.layout().addWidget(self.confirm_button)
		self.layout().addWidget(self.cancel_button)
		self.cancel_button.clicked.connect(self.reject)
		self.confirm_button.clicked.connect(self.accept)
		self.setWindowTitle('Select Profile')
		self.resize(350, 300)

	def get_selected_path(self) -> pathlib.Path:
		return self.profile_paths[self.profileListView.currentIndex().row()]


class MainWindow(QMainWindow):
	def __init__(self, state, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.tabWidget = QTabWidget()
		self.dashboardTab = tabs.Dashboard(state)
		self.databaseTab = tabs.Database(state)
		self.extensionsTab = tabs.Extensions(state)
		self.aboutTab = tabs.About(state)
		self.tabWidget.addTab(self.dashboardTab, 'Dashboard')
		self.tabWidget.addTab(self.databaseTab, 'Database')
		self.tabWidget.addTab(self.extensionsTab, 'Extensions')
		self.tabWidget.addTab(self.aboutTab, 'About')
		self.setCentralWidget(self.tabWidget)
		self.setWindowTitle('ChattyBoi')
		self.setMinimumSize(400, 200)
		self.resize(700, 500)
