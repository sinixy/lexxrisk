from dotenv import load_dotenv
import os
import json

load_dotenv()


BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_PATH = os.getenv('DB_PATH')
GSKEY_PATH = os.getenv('GSKEY_PATH')

WORKSHEET_CONFIG_PATH = os.getenv('WORKSHEET_CONFIG_PATH')
with open(WORKSHEET_CONFIG_PATH, encoding='utf-8') as f:
    _WS_DICT = json.load(f)

class RiskConfig:

    _DICT = _WS_DICT['risk']

    KEY = _DICT['key']
    TITLE = _DICT['title']

    NAME_COL = _DICT['columns']['name']
    ACCOUNT_COL = _DICT['columns']['account']
    STOP_COL = _DICT['columns']['stop']
    COVER_COL = _DICT['columns']['cover']

class FixerConfig:

    _DICT = _WS_DICT['fixer']

    KEY = _DICT['key']
    TITLE = _DICT['title']

    ACCOUNT_COL = _DICT['columns']['account']
    TRIGGER_COL = _DICT['columns']['trigger']
    STEP_COL = _DICT['columns']['step']

class TakionConfig:

    TOKEN = os.getenv('TAKION_TOKEN')
    HEADERS = {
        'Content-Type': 'application/json',
        'Authorization': TOKEN
    }
    BASE_URL = 'https://risk.itadviser.ee/api/v1/risks'