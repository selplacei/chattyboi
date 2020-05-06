import logging
import sys

from PySide2.QtCore import QSettings

qt_app_name = 'ChattyBoi'
qt_org_name = 'selplacei'

system_settings = QSettings(QSettings.SystemScope, qt_app_name, qt_org_name)
user_settings = QSettings(QSettings.UserScope, qt_app_name, qt_org_name)

log_format = '%(asctime)s:%(name)s: [%(levelname)s] %(message)s'
log_datefmt = '%H:%M:%S'
log_level = logging.DEBUG if '--debug' in sys.argv else logging.WARNING
