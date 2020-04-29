from PySide2.QtCore import QSettings

qt_app_name = 'ChattyBoi'
qt_org_name = 'selplacei'

system_settings = QSettings(QSettings.SystemScope, qt_app_name, qt_org_name)
user_settings = QSettings(QSettings.UserScope, qt_app_name, qt_org_name)
