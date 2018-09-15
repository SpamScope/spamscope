# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

from src.modules import (
    abstracts,
    attachments,
    bitmap,
    mails,
    networks,
    utils,
    MAIL_PATH)

DEFAULTS = {
    "SHODAN_ENABLED": "False",
    "SPAMASSASSIN_ENABLED": "False",
    "THUG_ENABLED": "False",
    "TIKA_APP_JAR": "/opt/tika/tika-app-1.18.jar",
    "VIRUSTOTAL_ENABLED": "False",
    "ZEMANA_ENABLED": "False",
}
