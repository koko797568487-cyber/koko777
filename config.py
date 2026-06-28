import threading

# ==================== BOT CONFIG ====================
BOT_TOKEN = "8917445664:AAFHICRJg7OyTP0L10ASo7dLJKD5cDRVoBg"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
API_BASE = "https://api.bigwinqaz.com/api/webapi/"

GAME_TYPES = {
    "1": {"name": "Wingo 30s",      "typeId": 30, "is_trx": False},
    "2": {"name": "Wingo 1 Minute", "typeId": 1,  "is_trx": False},
    "3": {"name": "TRX Wingo 1 Min", "typeId": 13, "is_trx": True},
}
DEFAULT_GAME_TYPE = "1"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://777bigwingame.vip",
    "Referer": "https://777bigwingame.vip/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ==================== SESSION STORAGE ====================
user_sessions = {}
session_lock = threading.Lock()

def get_default_session():
    return {
        'api': None, 'betting_sequence': [1, 2, 5, 11, 24, 53, 117, 258, 569],
        'base_amount': 10, 'current_step': 0, 'total_profit': 0.0,
        'is_running': False, 'last_known_balance': 0.0,
        'virtual_mode': False, 'virtual_balance': 10000.0,
        'stop_loss': 1564.0, 'profit_target': 10000.0,
        'game_key': DEFAULT_GAME_TYPE, 'strategy_mode': 'SIGMA',
        'last_sigma_index': '--', 'last_stability': '--',
        'bs_custom_sequence': ['B', 'B', 'S', 'S'], 'bs_custom_index': 0,
        'input_state': None
    }
