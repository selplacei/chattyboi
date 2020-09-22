import logging
import sys
from pathlib import Path

from PySide2.QtCore import QSettings

RESET = False

QT_APP_NAME = 'ChattyBoi'
QT_ORG_NAME = 'selplacei'

LOG_FORMAT = '%(asctime)s:%(name)s: [%(levelname)s] %(message)s'
LOG_DATEFMT = '%H:%M:%S'
LOG_LEVEL = logging.DEBUG if '--debug' in sys.argv else logging.WARNING

system_settings = QSettings(QSettings.SystemScope, QT_APP_NAME, QT_ORG_NAME)
user_settings = QSettings(QSettings.UserScope, QT_APP_NAME, QT_ORG_NAME)

_installation_path = Path('.').resolve()


def reset():
    system_settings.clear()
    user_settings.clear()
    user_settings.setValue('profile paths', [_installation_path])


if RESET:
    reset()
