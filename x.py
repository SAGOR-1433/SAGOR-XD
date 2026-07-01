import time
import requests
import json
import re
import os
from datetime import datetime, date, timedelta
from urllib.parse import quote_plus
from pathlib import Path
import sqlite3
import telebot
from telebot import types
import threading
import random
import itertools

# --- الإعدادات الجديدة للوحة المطلوبة ---
BASE = "https://flysms.net"
AJAX_PATH = "/client/res/data_smscdr.php" 
LOGIN_PAGE_URL = BASE + "/login"
LOGIN_POST_URL = BASE + "/signin"

# ======================
# لوحات متعددة (تم تحديثها للوحة الجديدة flysms.net)
# ======================
DASHBOARD_CONFIGS = [
    {
        "name": "Fly SMS Global",
        "base": "https://flysms.net",
        "ajax_path": "/client/res/data_smscdr.php",
        "login_page": "/login",
        "login_post": "/signin",
        "username": "User01",
        "password": "User01",
        "type": "CAPTCHA", 
        "session": requests.Session(),
        "is_logged_in": False,
        "stats_page": "/client/SMSCDRStats",
        "sesskey": None
    }
]

# تهيئة headers موحدة
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8"
}

for dash in DASHBOARD_CONFIGS:
    dash["session"].headers.update(COMMON_HEADERS)
    login_page_url = dash["base"] + dash["login_page"]
    dash["login_page_url"] = login_page_url
    dash["login_post_url"] = dash["base"] + dash["login_post"]
    dash["ajax_url"] = dash["base"] + dash["ajax_path"]

# الإعدادات العامة للبوت (تم تحديثها ببياناتك الجديدة)
USERNAME = "User01"
PASSWORD = "User01"
BOT_TOKEN = "8403748948:AAE0eqO_aZNw8SO52ytgutT1p1Cw8DXX4Gw"
CHAT_IDS = ["-1003506005850"]

# فحص إعدادات البوت
print("\n🔧 فحص إعدادات البوت:")
print(f"✅ BOT_TOKEN: {'محدد' if BOT_TOKEN else 'غير محدد'}")
print(f"✅ عدد CHAT_IDS: {len(CHAT_IDS)}")

REFRESH_INTERVAL = 5
TIMEOUT = 30
MAX_RETRIES = 5
RETRY_DELAY = 5
IDX_DATE = 0
IDX_NUMBER = 2
IDX_SMS = 5
SENT_MESSAGES_FILE = "sent_messages.json"

ADMIN_IDS = [7858001619,7244951433]
DB_PATH = "bot.db"

def is_admin(user_id):
    return user_id in ADMIN_IDS

bot = telebot.TeleBot(BOT_TOKEN)

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN must be set in Secrets (Environment Variables)")
if not CHAT_IDS:
    raise SystemExit("❌ CHAT_IDS must be configured")
if not USERNAME or not PASSWORD:
    print("⚠️  WARNING: SITE_USERNAME and SITE_PASSWORD not set in Secrets")
    print("⚠️  Bot will continue but login may fail")

COUNTRY_CODES = {
    "1": ("USA/Canada", "🇺🇸", "USA/CANADA"),
    "7": ("Kazakhstan ", "🇰🇿", "KAZAKHSTAN"),
    "20": ("Egypt", "🇪🇬", "EGYPT"),
    "27": ("South Africa", "🇿🇦", "SOUTH AFRICA"),
    "30": ("Greece", "🇬🇷", "GREECE"),
    "31": ("Netherlands", "🇳🇱", "NETHERLANDS"),
    "32": ("Belgium", "🇧🇪", "BELGIUM"),
    "33": ("France", "🇫🇷", "FRANCE"),
    "34": ("Spain", "🇪🇸", "SPAIN"),
    "36": ("Hungary", "🇭🇺", "HUNGARY"),
    "39": ("Italy", "🇮🇹", "ITALY"),
    "40": ("Romania", "🇷🇴", "ROMANIA"),
    "41": ("Switzerland", "🇨🇭", "SWITZERLAND"),
    "43": ("Austria", "🇦🇹", "AUSTRIA"),
    "44": ("UK", "🇬🇧", "UK"),
    "45": ("Denmark", "🇩🇰", "DENMARK"),
    "46": ("Sweden", "🇸🇪", "SWEDEN"),
    "47": ("Norway", "🇳🇴", "NORWAY"),
    "48": ("Poland", "🇵🇱", "POLAND"),
    "49": ("Germany", "🇩🇪", "GERMANY"),
    "51": ("Peru", "🇵🇪", "PERU"),
    "52": ("Mexico", "🇲🇽", "MEXICO"),
    "53": ("Cuba", "🇨🇺", "CUBA"),
    "54": ("Argentina", "🇦🇷", "ARGENTINA"),
    "55": ("Brazil", "🇧🇷", "BRAZIL"),
    "56": ("Chile", "🇨🇱", "CHILE"),
    "57": ("Colombia", "🇨🇴", "COLOMBIA"),
    "58": ("Venezuela", "🇻🇪", "VENEZUELA"),
    "60": ("Malaysia", "🇲🇾", "MALAYSIA"),
    "61": ("Australia", "🇦🇺", "AUSTRALIA"),
    "62": ("Indonesia", "🇮🇩", "INDONESIA"),
    "63": ("Philippines", "🇵🇭", "PHILIPPINES"),
    "64": ("New Zealand", "🇳🇿", "NEW ZEALAND"),
    "65": ("Singapore", "🇸🇬", "SINGAPORE"),
    "66": ("Thailand", "🇹🇭", "THAILAND"),
    "81": ("Japan", "🇯🇵", "JAPAN"),
    "82": ("South Korea", "🇰🇷", "SOUTH KOREA"),
    "84": ("Vietnam", "🇻🇳", "VIETNAM"),
    "86": ("China", "🇨🇳", "CHINA"),
    "90": ("Turkey", "🇹🇷", "TURKEY"),
    "91": ("India", "🇮🇳", "INDIA"),
    "92": ("Pakistan", "🇵🇰", "PAKISTAN"),
    "93": ("Afghanistan", "🇦🇫", "AFGHANISTAN"),
    "94": ("Sri Lanka", "🇱🇰", "SRI LANKA"),
    "95": ("Myanmar", "🇲🇲", "MYANMAR"),
    "98": ("Iran", "🇮🇷", "IRAN"),
    "211": ("South Sudan", "🇸🇸", "SOUTH SUDAN"),
    "212": ("Morocco", "🇲🇦", "MOROCCO"),
    "213": ("Algeria", "🇩🇿", "ALGERIA"),
    "216": ("Tunisia", "🇹🇳", "TUNISIA"),
    "218": ("Libya", "🇱🇾", "LIBYA"),
    "220": ("Gambia", "🇬🇲", "GAMBIA"),
    "221": ("Senegal", "🇸🇳", "SENEGAL"),
    "222": ("Mauritania", "🇲🇷", "MAURITANIA"),
    "223": ("Mali", "🇲🇱", "MALI"),
    "224": ("Guinea", "🇬🇳", "GUINEA"),
    "225": ("Ivory Coast", "🇨🇮", "IVORY COAST"),
    "226": ("Burkina Faso", "🇧🇫", "BURKINA FASO"),
    "227": ("Niger", "🇳🇪", "NIGER"),
    "228": ("Togo", "🇹🇬", "TOGO"),
    "229": ("Benin", "🇧🇯", "BENIN"),
    "230": ("Mauritius", "🇲🇺", "MAURITIUS"),
    "231": ("Liberia", "🇱🇷", "LIBERIA"),
    "232": ("Sierra Leone", "🇸🇱", "SIERRA LEONE"),
    "233": ("Ghana", "🇬🇭", "GHANA"),
    "234": ("Nigeria", "🇳🇬", "NIGERIA"),
    "235": ("Chad", "🇹🇩", "CHAD"),
    "236": ("CAR", "🇨🇫", "CENTRAL AFRICAN REP"),
    "237": ("Cameroon", "🇨🇲", "CAMEROON"),
    "238": ("Cape Verde", "🇨🇻", "CAPE VERDE"),
    "239": ("Sao Tome", "🇸🇹", "SAO TOME"),
    "240": ("Eq. Guinea", "🇬🇶", "EQUATORIAL GUINEA"),
    "241": ("Gabon", "🇬🇦", "GABON"),
    "242": ("Congo", "🇨🇬", "CONGO"),
    "243": ("DR Congo", "🇨🇩", "DR CONGO"),
    "244": ("Angola", "🇦🇴", "ANGOLA"),
    "245": ("Guinea-Bissau", "🇬🇼", "GUINEA-BISSAU"),
    "248": ("Seychelles", "🇸🇨", "SEYCHELLES"),
    "249": ("Sudan", "🇸🇩", "SUDAN"),
    "250": ("Rwanda", "🇷🇼", "RWANDA"),
    "251": ("Ethiopia", "🇪🇹", "ETHIOPIA"),
    "252": ("Somalia", "🇸🇴", "SOMALIA"),
    "253": ("Djibouti", "🇩🇯", "DJIBOUTI"),
    "254": ("Kenya", "🇰🇪", "KENYA"),
    "255": ("Tanzania", "🇹🇿", "TANZANIA"),
    "256": ("Uganda", "🇺🇬", "UGANDA"),
    "257": ("Burundi", "🇧🇮", "BURUNDI"),
    "258": ("Mozambique", "🇲🇿", "MOZAMBIQUE"),
    "260": ("Zambia", "🇿🇲", "ZAMBIA"),
    "261": ("Madagascar", "🇲🇬", "MADAGASCAR"),
    "262": ("Reunion", "🇷🇪", "REUNION"),
    "263": ("Zimbabwe", "🇿🇼", "ZIMBABWE"),
    "264": ("Namibia", "🇳🇦", "NAMIBIA"),
    "265": ("Malawi", "🇲🇼", "MALAWI"),
    "266": ("Lesotho", "🇱🇸", "LESOTHO"),
    "267": ("Botswana", "🇧🇼", "BOTSWANA"),
    "268": ("Eswatini", "🇸🇿", "ESWATINI"),
    "269": ("Comoros", "🇰🇲", "COMOROS"),
    "350": ("Gibraltar", "🇬🇮", "GIBRALTAR"),
    "351": ("Portugal", "🇵🇹", "PORTUGAL"),
    "352": ("Luxembourg", "🇱🇺", "LUXEMBOURG"),
    "353": ("Ireland", "🇮🇪", "IRELAND"),
    "354": ("Iceland", "🇮🇸", "ICELAND"),
    "355": ("Albania", "🇦🇱", "ALBANIA"),
    "356": ("Malta", "🇲🇹", "MALTA"),
    "357": ("Cyprus", "🇨🇾", "CYPRUS"),
    "358": ("Finland", "🇫🇮", "FINLAND"),
    "359": ("Bulgaria", "🇧🇬", "BULGARIA"),
    "370": ("Lithuania", "🇱🇹", "LITHUANIA"),
    "371": ("Latvia", "🇱🇻", "LATVIA"),
    "372": ("Estonia", "🇪🇪", "ESTONIA"),
    "373": ("Moldova", "🇲🇩", "MOLDOVA"),
    "374": ("Armenia", "🇦🇲", "ARMENIA"),
    "375": ("Belarus", "🇧🇾", "BELARUS"),
    "376": ("Andorra", "🇦🇩", "ANDORRA"),
    "377": ("Monaco", "🇲🇨", "MONACO"),
    "378": ("San Marino", "🇸🇲", "SAN MARINO"),
    "380": ("Ukraine", "🇺🇦", "UKRAINE"),
    "381": ("Serbia", "🇷🇸", "SERBIA"),
    "382": ("Montenegro", "🇲🇪", "MONTENEGRO"),
    "383": ("Kosovo", "🇽🇰", "KOSOVO"),
    "385": ("Croatia", "🇭🇷", "CROATIA"),
    "386": ("Slovenia", "🇸🇮", "SLOVENIA"),
    "387": ("Bosnia", "🇧🇦", "BOSNIA"),
    "389": ("N. Macedonia", "🇲🇰", "NORTH MACEDONIA"),
    "420": ("Czech Rep", "🇨🇿", "CZECH REPUBLIC"),
    "421": ("Slovakia", "🇸🇰", "SLOVAKIA"),
    "423": ("Liechtenstein", "🇱🇮", "LIECHTENSTEIN"),
    "500": ("Falkland", "🇫🇰", "FALKLAND ISLANDS"),
    "501": ("Belize", "🇧🇿", "BELIZE"),
    "502": ("Guatemala", "🇬🇹", "GUATEMALA"),
    "503": ("El Salvador", "🇸🇻", "EL SALVADOR"),
    "504": ("Honduras", "🇭🇳", "HONDURAS"),
    "505": ("Nicaragua", "🇳🇮", "NICARAGUA"),
    "506": ("Costa Rica", "🇨🇷", "COSTA RICA"),
    "507": ("Panama", "🇵🇦", "PANAMA"),
    "509": ("Haiti", "🇭🇹", "HAITI"),
    "591": ("Bolivia", "🇧🇴", "BOLIVIA"),
    "592": ("Guyana", "🇬🇾", "GUYANA"),
    "593": ("Ecuador", "🇪🇨", "ECUADOR"),
    "595": ("Paraguay", "🇵🇾", "PARAGUAY"),
    "597": ("Suriname", "🇸🇷", "SURINAME"),
    "598": ("Uruguay", "🇺🇾", "URUGUAY"),
    "670": ("Timor-Leste", "🇹🇱", "TIMOR-LESTE"),
    "673": ("Brunei", "🇧🇳", "BRUNEI"),
    "674": ("Nauru", "🇳🇷", "NAURU"),
    "675": ("PNG", "🇵🇬", "PAPUA NEW GUINEA"),
    "676": ("Tonga", "🇹🇴", "TONGA"),
    "677": ("Solomon Is", "🇸🇧", "SOLOMON ISLANDS"),
    "678": ("Vanuatu", "🇻🇺", "VANUATU"),
    "679": ("Fiji", "🇫🇯", "FIJI"),
    "680": ("Palau", "🇵🇼", "PALAU"),
    "685": ("Samoa", "🇼🇸", "SAMOA"),
    "686": ("Kiribati", "🇰🇮", "KIRIBATI"),
    "687": ("New Caledonia", "🇳🇨", "NEW CALEDONIA"),
    "688": ("Tuvalu", "🇹🇻", "TUVALU"),
    "689": ("Fr Polynesia", "🇵🇫", "FRENCH POLYNESIA"),
    "691": ("Micronesia", "🇫🇲", "MICRONESIA"),
    "692": ("Marshall Is", "🇲🇭", "MARSHALL ISLANDS"),
    "850": ("North Korea", "🇰🇵", "NORTH KOREA"),
    "852": ("Hong Kong", "🇭🇰", "HONG KONG"),
    "853": ("Macau", "🇲🇴", "MACAU"),
    "855": ("Cambodia", "🇰🇭", "CAMBODIA"),
    "856": ("Laos", "🇱🇦", "LAOS"),
    "960": ("Maldives", "🇲🇻", "MALDIVES"),
    "961": ("Lebanon", "🇱🇧", "LEBANON"),
    "962": ("Jordan", "🇯🇴", "JORDAN"),
    "963": ("Syria", "🇸🇾", "SYRIA"),
    "964": ("Iraq", "🇮🇶", "IRAQ"),
    "965": ("Kuwait", "🇰🇼", "KUWAIT"),
    "966": ("Saudi Arabia", "🇸🇦", "SAUDI ARABIA"),
    "967": ("Yemen", "🇾🇪", "YEMEN"),
    "968": ("Oman", "🇴🇲", "OMAN"),
    "970": ("Palestine", "🇵🇸", "PALESTINE"),
    "971": ("UAE", "🇦🇪", "UAE"),
    "972": ("Israel", "🇮🇱", "ISRAEL"),
    "973": ("Bahrain", "🇧🇭", "BAHRAIN"),
    "974": ("Qatar", "🇶🇦", "QATAR"),
    "975": ("Bhutan", "🇧🇹", "BHUTAN"),
    "976": ("Mongolia", "🇲🇳", "MONGOLIA"),
    "977": ("Nepal", "🇳🇵", "NEPAL"),
    "992": ("Tajikistan", "🇹🇯", "TAJIKISTAN"),
    "993": ("Turkmenistan", "🇹🇲", "TURKMENISTAN"),
    "994": ("Azerbaijan", "🇦🇿", "AZERBAIJAN"),
    "995": ("Georgia", "🇬🇪", "GEORGIA"),
    "996": ("Kyrgyzstan", "🇰🇬", "KYRGYZSTAN"),
    "998": ("Uzbekistan", "🇺🇿", "UZBEKISTAN"),
}

# ======================
# دوال إدارة قاعدة البيانات
# ======================
def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # إنشاء جدول users بدون selected_app
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            country_code TEXT,
            assigned_number TEXT,
            is_banned INTEGER DEFAULT 0,
            private_combo_country TEXT DEFAULT NULL
        )
    ''')
    
    # إنشاء جدول combos مع اسم مخصص
    c.execute('''
        CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            combo_name TEXT,
            country_code TEXT,
            numbers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            otp TEXT,
            full_message TEXT,
            timestamp TEXT,
            assigned_to INTEGER
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS private_combos (
            user_id INTEGER,
            country_code TEXT,
            numbers TEXT,
            PRIMARY KEY (user_id, country_code)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS force_sub_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, username="", first_name="", last_name="", country_code=None, assigned_number=None, private_combo_country=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    existing_data = get_user(user_id)
    if existing_data:
        if country_code is None:
            country_code = existing_data[4]
        if assigned_number is None:
            assigned_number = existing_data[5]
        if private_combo_country is None:
            private_combo_country = existing_data[7]

    c.execute("""
        REPLACE INTO users (user_id, username, first_name, last_name, country_code, assigned_number, is_banned, private_combo_country)
        VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE user_id=?), 0), ?)
    """, (
        user_id,
        username,
        first_name,
        last_name,
        country_code,
        assigned_number,
        user_id,
        private_combo_country
    ))
    conn.commit()
    conn.close()

def ban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[6] == 1

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_combo_by_id(combo_id):
    """جلب كومبو بواسطة ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, combo_name, country_code, numbers FROM combos WHERE id=?", (combo_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "country_code": row[2],
            "numbers": json.loads(row[3]) if row[3] else []
        }
    return None

def get_combo(country_code, user_id=None):
    """جلب كومبو"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # أولاً: كومبو خاص بالمستخدم
    if user_id:
        c.execute("SELECT numbers FROM private_combos WHERE user_id=? AND country_code=?", 
                  (user_id, country_code))
        row = c.fetchone()
        if row:
            conn.close()
            return json.loads(row[0]) if row[0] else []
    
    # ثانياً: كومبو عام
    c.execute("SELECT numbers FROM combos WHERE country_code=? ORDER BY id DESC LIMIT 1", (country_code,))
    row = c.fetchone()
    conn.close()
    
    return json.loads(row[0]) if row and row[0] else []

def save_combo(combo_name, country_code, numbers, user_id=None):
    """حفظ كومبو جديد مع اسم مخصص"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if user_id:
        # كومبو خاص بالمستخدم
        c.execute("REPLACE INTO private_combos (user_id, country_code, numbers) VALUES (?, ?, ?)",
                  (user_id, country_code, json.dumps(numbers)))
        print(f"✅ تم حفظ كومبو خاص للمستخدم {user_id} - الدولة {country_code}")
    else:
        # كومبو عام للجميع
        c.execute("INSERT INTO combos (combo_name, country_code, numbers) VALUES (?, ?, ?)",
                  (combo_name.strip(), country_code, json.dumps(numbers)))
        print(f"✅ تم حفظ كومبو عام - الاسم: {combo_name} - الدولة: {country_code}")
    
    conn.commit()
    conn.close()

def delete_combo_by_id(combo_id):
    """حذف كومبو بواسطة ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("DELETE FROM combos WHERE id=?", (combo_id,))
    deleted = c.rowcount > 0
    
    conn.commit()
    conn.close()
    return deleted

def get_all_combos_with_names():
    """جلب جميع الكومبوهات مع أسمائها"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id, combo_name, country_code, numbers FROM combos ORDER BY combo_name")
    combos = c.fetchall()
    
    conn.close()
    return combos

def normalize_phone_number(number):
    """توحيد تنسيق أرقام الهواتف"""
    if not number:
        return ""
    
    # تحويل إلى نص
    number_str = str(number)
    
    # إزالة جميع الرموز غير رقمية
    number_str = re.sub(r'\D', '', number_str)
    
    # إذا كان الرقم فارغاً بعد التنظيف
    if not number_str:
        return ""
    
    return number_str

def assign_number_to_user(user_id, number):
    """تعيين رقم للمستخدم مع تطبيع التنسيق"""
    normalized = normalize_phone_number(number)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (normalized, user_id))
    conn.commit()
    conn.close()

def debug_user_numbers():
    """عرض جميع الأرقام المخزنة للمستخدمين للتشخيص"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
    rows = c.fetchall()
    conn.close()
    
    print("\n🔍 تصحيح أرقام المستخدمين:")
    print("=" * 50)
    for user_id, number in rows:
        normalized = normalize_phone_number(number)
        print(f"المستخدم {user_id}: {number} → {normalized}")
    print("=" * 50)
    return len(rows)

def get_user_by_number(number):
    """البحث عن المستخدم برقم هاتف (مع تطبيع التنسيق)"""
    if not number:
        print(f"⚠️ رقم فارغ في البحث")
        return None
    
    # تطبيع الرقم المدخل
    normalized = normalize_phone_number(number)
    if not normalized:
        print(f"⚠️ رقم غير صالح بعد التطبيع: {number}")
        return None
    
    print(f"🔍 البحث عن الرقم المطبيع: {normalized}")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. أولاً: البحث المباشر بالرقم المطبيع
    c.execute("SELECT user_id FROM users WHERE assigned_number = ?", (normalized,))
    row = c.fetchone()
    if row:
        print(f"✅ وجد مباشرةً بالمطابقة التامة: المستخدم {row[0]}")
        conn.close()
        return row[0]
    
    # 2. ثانياً: البحث في جميع الأرقام المخزنة
    c.execute("SELECT user_id, assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
    all_users = c.fetchall()
    conn.close()
    
    print(f"📊 عدد المستخدمين في قاعدة البيانات: {len(all_users)}")
    
    for user_row in all_users:
        user_id, db_number = user_row
        if not db_number:
            continue
            
        # تطبيع الرقم المخزن
        db_normalized = normalize_phone_number(db_number)
        
        # مقارنة بعدة طرق
        if db_normalized == normalized:
            print(f"✅ تطابق بعد التطبيع: المستخدم {user_id}")
            return user_id
        elif normalized in db_normalized:
            print(f"✅ الرقم المطلوب جزء من الرقم المخزن: المستخدم {user_id}")
            return user_id
        elif db_normalized in normalized:
            print(f"✅ الرقم المخزن جزء من الرقم المطلوب: المستخدم {user_id}")
            return user_id
    
    print(f"❌ لم يتم العثور على المستخدم للرقم: {normalized}")
    return None

def log_otp(number, otp, full_message, assigned_to=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO otp_logs (number, otp, full_message, timestamp, assigned_to) VALUES (?, ?, ?, ?, ?)",
              (number, otp, full_message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), assigned_to))
    conn.commit()
    conn.close()

def release_number(old_number):
    if not old_number:
        return
    # تطبيع الرقم أولاً
    normalized = normalize_phone_number(old_number)
    if not normalized:
        return
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # محاولة البحث بالرقم المطبيع
    c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (normalized,))
    
    # إذا لم يتم تحديث أي صف، جرب البحث بالرقم كما هو
    if c.rowcount == 0:
        c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (old_number,))
    
    if c.rowcount > 0:
        print(f"✅ تم تحرير الرقم: {old_number}")
    
    conn.commit()
    conn.close()

def get_otp_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM otp_logs")
    logs = c.fetchall()
    conn.close()
    return logs

def get_user_info(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

# ======================
# دوال الاشتراك الإجباري
# ======================
def get_all_force_sub_channels(enabled_only=True):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if enabled_only:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels WHERE enabled = 1 ORDER BY id")
    else:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def add_force_sub_channel(channel_url, description=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, 1)",
                  (channel_url.strip(), description.strip()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_force_sub_channel(channel_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM force_sub_channels WHERE id = ?", (channel_id,))
    changed = c.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def toggle_force_sub_channel(channel_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE force_sub_channels SET enabled = 1 - enabled WHERE id = ?", (channel_id,))
    conn.commit()
    conn.close()

def force_sub_check(user_id):
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return True

    for _, url, _ in channels:
        try:
            if url.startswith("https://t.me/"):
                ch = "@" + url.split("/")[-1]
            elif url.startswith("@"):
                ch = url
            else:
                continue
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"[!] خطأ في التحقق من القناة {url}: {e}")
            return False
    return True

def force_sub_markup():
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return None

    markup = types.InlineKeyboardMarkup()
    for _, url, desc in channels:
        text = f"📢 {desc}" if desc else "📢 اشترك في القناة"
        markup.add(types.InlineKeyboardButton(text, url=url))
    markup.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub"))
    return markup

# ======================
# دوال التنسيق
# ======================
def html_escape(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

def mask_number(number):
    if not number:
        return "N/A"
    
    number_str = str(number).strip()
    
    # إذا كان الرقم قصير جداً، أرجع كما هو
    if len(number_str) <= 8:
        return number_str
    
    # تأكد أن الرقم طويل بما يكفي للإخفاء
    if len(number_str) >= 11:
        # إخفاء الأرقام الوسطى
        return number_str[:7] + "••" + number_str[-4:]
    elif len(number_str) >= 9:
        # إذا كان الرقم بين 9 و 10 أرقام
        return number_str[:4] + "••" + number_str[-4:]
    else:
        return number_str

def extract_otp(message):
    complex_match = re.search(r'(\d{3,4})[\s\-\\](\d{3,4})', message)
    if complex_match:
        return f"{complex_match.group(1)}-{complex_match.group(2)}"

    patterns = [
        r'(?:code|رمز|كود|otp|pin)[:\s]+[‎]?(\d{6,8})',
        r'\b(\d{6,8})\b'
    ]
    for p in patterns:
        match = re.search(p, message, re.IGNORECASE)
        if match:
            return match.group(1)
    return "N/A"

def detect_service(message):
    message_lower = message.lower()
    services = {
        "#WP": ["whatsapp", "واتساب", "واتس"],
        "#FB": ["facebook", "فيسبوك", "fb"],
        "#IG": ["instagram", "انستقرام", "انستا"],
        "#TG": ["telegram", "تيليجرام"],
        "#TW": ["twitter", "تويتر"],
        "#GG": ["google", "gmail", "جوجل"],
        "#DC": ["discord"],
        "#LN": ["line"],
        "#VB": ["viber"],
        "#SK": ["skype"],
        "#SC": ["snapchat"],
        "#TT": ["tiktok", "tik tok"],
        "#AMZ": ["amazon"],
        "#APL": ["apple"],
        "#MS": ["microsoft"],
        "#IN": ["linkedin"],
        "#UB": ["uber"],
        "#AB": ["airbnb", "air bnb"],
        "#NF": ["netflix"],
        "#SP": ["spotify"],
        "#YT": ["youtube"],
        "#GH": ["github"],
        "#PT": ["pinterest"],
        "#PP": ["paypal"],
        "#BK": ["booking"],
    }
    for service, keywords in services.items():
        for keyword in keywords:
            if keyword in message_lower:
                return service.upper()
    return "GENERAL"

def format_message_for_user(date_str, number, sms):
    """تنسيق رسالة OTP للمستخدم في الخاص"""
    country_name, country_flag, country_upper = get_country_info(number)
    otp_code = extract_otp(sms)
    service = detect_service(sms)
    
    # تنسيق جديد مشابه للكود الثاني
    message = f"☎️ Your Number: {number}\n"
    message += f"🔑OTP: {otp_code}\n"
    message += f"💬 Service : {service}"
    
    return message

def format_message_for_channel(date_str, number, sms):
    """تنسيق رسالة OTP للقناة"""
    country_name, country_flag, country_upper = get_country_info(number)
    masked_num = mask_number(number)
    otp_code = extract_otp(sms)
    service = detect_service(sms)
    
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        formatted_time = date_str
    
    # تنسيق رسالة القناة
    if otp_code != "N/A":
        otp_display = otp_code
    else:
        otp_display = "N/A"
    
    sms_escaped = html_escape(sms)
    
    message = f"{country_flag} <b><u>{country_name}</u></b> {service} <b><u>{masked_num}</u></b>\n\n"
    message += f"<pre><code>{sms_escaped}</code></pre>\n\n"
    message += f"⏰ <i>{formatted_time}</i>"
    
    return message

def format_number_assigned_message(number, country_code, combo_name=""):
    """تنسيق رسالة تعيين الرقم للمستخدم"""
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    formatted_number = number
    
    # إضافة اسم الكومبو إذا كان موجوداً
    combo_text = f" - {combo_name}" if combo_name else ""
    
    # تنسيق جديد
    message = f"📞 Your Number From {flag} {name}{combo_text} : `{formatted_number}`\n\n"
    message += "Waiting for OTP.…🔑\n\n"
    message += "_🚨 The OTP will be sent to you here_"
    
    return message

def format_admin_panel():
    """تنسيق لوحة التحكم الإدارية"""
    message = "🔐 ♛ 𝘾𝙤𝙢𝙢𝙖𝙣𝙙𝙤 𝗢𝗧𝗣 ♛\n— 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 —"
    return message

# ======================
# دالة إرسال Telegram
# ======================
def delete_message_after_delay(chat_id, message_id, delay=20):
    """حذف الرسالة بعد تأخير معين"""
    def delete():
        try:
            time.sleep(delay)
            bot.delete_message(chat_id, message_id)
            print(f"🗑️ تم حذف الرسالة {message_id} من {chat_id} بعد {delay} ثانية")
        except Exception as e:
            print(f"❌ فشل حذف الرسالة {message_id}: {e}")
    
    threading.Thread(target=delete).start()

def send_to_telegram_group(text, otp_code):
    """إرسال رسالة إلى القناة مع زر نسخ OTP"""
    if not BOT_TOKEN:
        print("❌ خطأ: BOT_TOKEN غير محدد!")
        return False
    
    if not CHAT_IDS:
        print("❌ خطأ: CHAT_IDS فارغ!")
        return False
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "𝐂𝐨𝐧𝐭𝐚𝐜𝐭 𝐃𝐞𝐯𝐞𝐥𝐨𝐩𝐞𝐫 📩", "url": "https://t.me/CM_ED871"},
                {"text": "𝐆𝐞𝐭 𝐍𝐮𝐦𝐛𝐞𝐫 📞", "url": "https://t.me/Commandoop_bot"}
            ],
            [
                {
                    "text": otp_code,
                    "copy_text": {"text": otp_code}
                }
            ]
        ]
    }
    
    success_count = 0
    
    for idx, chat_id in enumerate(CHAT_IDS):
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard),
                "disable_web_page_preview": True
            }
            
            resp = requests.post(url, data=payload, timeout=15)
            
            if resp.status_code == 200:
                success_count += 1
                result_json = resp.json()
                message_id = result_json.get("result", {}).get("message_id")
                print(f"✅ تم إرسال الرسالة إلى القناة {chat_id}")
                
                # إضافة خاصية الحذف التلقائي بعد 20 ثانية
                # if message_id:
                #     delete_message_after_delay(chat_id, message_id, 20)
            else:
                print(f"❌ فشل إرسال إلى {chat_id}: {resp.status_code} - {resp.text}")
                
        except Exception as e:
            print(f"🚨 استثناء أثناء الإرسال إلى {chat_id}: {type(e).__name__} - {str(e)}")
    
    return success_count > 0

# ======================
# وظائف البوت التفاعلي
# ======================
user_states = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 You are banned.")
        return
    
    if not force_sub_check(message.from_user.id):
        markup = force_sub_markup()
        if markup:
            bot.send_message(message.chat.id, "🔒 You must subscribe to the channel.", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "🔒 Force sub enabled but no channel set!")
        return
    
    if not get_user(message.from_user.id):
        for admin in ADMIN_IDS:
            try:
                caption = f"🆕 New user booted:\n🆔: `{message.from_user.id}`\n👤: @{message.from_user.username or 'None'}\nName: {message.from_user.first_name or ''} {message.from_user.last_name or ''}"
                bot.send_message(admin, caption, parse_mode="Markdown")
            except:
                pass
    
    save_user(
        message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or ""
    )
    
    show_main_menu(message.chat.id)

def show_main_menu(chat_id, message_id=None):
    """عرض القائمة الرئيسية (الدول فقط)"""
    message  = " •𝘾𝙤𝙢𝙢𝙖𝙣𝙙𝙤 𝗢𝗧𝗣\n"
    message += "━━━━━━━━━━━━━━━━━━\n\n"
    message += "✨ 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝘾𝙤𝙢𝙢𝙖𝙣𝙙𝙤 𝗢𝗧𝗣 ✨\n\n"
    message += "𓍹𓍻 𝗦𝗘𝗟𝗘𝗖𝗧 𝗔 𝗖𝗢𝗨𝗡𝗧𝗥𝗬 ??𓍻\n\n"
    message += "🔐 𝗙𝗔𝗦𝗧 • 𝗦𝗘𝗖𝗨𝗥𝗘 • 𝗥𝗘𝗟𝗜𝗔𝗕𝗟𝗘\n"
    message += "━━━━━━━━━━━━━━━━━━\n"
    # جلب جميع الكومبوهات المتاحة
    combos = get_all_combos_with_names()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if not combos:
        markup.add(types.InlineKeyboardButton("📭 No Countries Available", callback_data="no_country"))
    else:
        buttons = []
        for combo in combos:
            combo_id, combo_name, country_code, _ = combo
            if country_code in COUNTRY_CODES:
                name, flag, _ = COUNTRY_CODES[country_code]
                display_name = f"{flag} {combo_name}" if combo_name else f"{flag} {name}"
                buttons.append(types.InlineKeyboardButton(
                    display_name, 
                    callback_data=f"combo_{combo_id}"
                ))
        
        # ترتيب الأزرار
        for i in range(0, len(buttons), 2):
            markup.row(*buttons[i:i+2])
    
    # زر المسؤولين فقط
    user_id = chat_id if isinstance(chat_id, int) else chat_id
    if user_id and is_admin(user_id):
        markup.row(
            types.InlineKeyboardButton("📊 KONEKTA Messages", callback_data="view_msgs_KONEKTA!!"),
            types.InlineKeyboardButton("📊 D-Group Messages", callback_data="view_msgs_D-Group")
        )
        markup.row(
            types.InlineKeyboardButton("📊 SMS-Dialer Messages", callback_data="view_msgs_SMS-Dialer")
        )
        markup.add(types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel"))
    
    if message_id:
        try:
            bot.edit_message_text(message, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        except:
            bot.send_message(chat_id, message, reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(chat_id, message, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    if force_sub_check(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Subscription verified! You can use the bot now.", show_alert=True)
        show_main_menu(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ You have not subscribed yet!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("combo_"))
def handle_combo_selection(call):
    if is_banned(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 You are banned.", show_alert=True)
        return
    
    if not force_sub_check(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ You must subscribe first!", show_alert=True)
        return
    
    combo_id = int(call.data.split("_", 1)[1])
    combo_data = get_combo_by_id(combo_id)
    
    if not combo_data:
        bot.answer_callback_query(call.id, "❌ Combo not found!", show_alert=True)
        return
    
    country_code = combo_data["country_code"]
    available_numbers = get_available_numbers(country_code, call.from_user.id)
    
    if not available_numbers:
        bot.edit_message_text("❌ All numbers are currently in use.", call.message.chat.id, call.message.message_id)
        return
    
    assigned = random.choice(available_numbers)
    old_user = get_user(call.from_user.id)
    
    if old_user and old_user[5]:
        release_number(old_user[5])
    
    assign_number_to_user(call.from_user.id, assigned)
    save_user(call.from_user.id, country_code=country_code, assigned_number=assigned)
    
    msg_text = format_number_assigned_message(assigned, country_code, combo_data["name"])
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Change Number", callback_data=f"change_num_{combo_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Change Country", callback_data="back_to_main"))
    
    bot.edit_message_text(msg_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    show_main_menu(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_num_"))
def change_number(call):
    if is_banned(call.from_user.id):
        return
    
    if not force_sub_check(call.from_user.id):
        return
    
    combo_id = int(call.data.split("_", 2)[2])
    combo_data = get_combo_by_id(combo_id)
    
    if not combo_data:
        bot.answer_callback_query(call.id, "❌ Combo not found!", show_alert=True)
        return
    
    country_code = combo_data["country_code"]
    available_numbers = get_available_numbers(country_code, call.from_user.id)
    
    if not available_numbers:
        bot.answer_callback_query(call.id, "❌ All numbers are in use.", show_alert=True)
        return
    
    old_user = get_user(call.from_user.id)
    if old_user and old_user[5]:
        release_number(old_user[5])
    
    assigned = random.choice(available_numbers)
    assign_number_to_user(call.from_user.id, assigned)
    save_user(call.from_user.id, assigned_number=assigned)
    
    msg_text = format_number_assigned_message(assigned, country_code, combo_data["name"])
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Change Number", callback_data=f"change_num_{combo_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Change Country", callback_data="back_to_main"))
    
    bot.edit_message_text(msg_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def handle_copy_otp(call):
    """معالجة زر نسخ OTP"""
    otp_code = call.data.split("_", 1)[1]
    
    # إرسال إشعار بنسخ النص
    bot.answer_callback_query(
        call.id,
        text=f"✅ تم نسخ OTP: {otp_code}",
        show_alert=True
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_msgs_"))
def handle_view_messages(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 Admin only!", show_alert=True)
        return

    dash_name = call.data.replace("view_msgs_", "")
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("📅 Today", callback_data=f"get_msgs_{dash_name}_today"),
        types.InlineKeyboardButton("📅 Yesterday", callback_data=f"get_msgs_{dash_name}_yesterday")
    )
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_main"))
    
    bot.edit_message_text(f"📊 Select period for <b>{dash_name}</b>:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("get_msgs_"))
def handle_get_messages(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 Admin only!", show_alert=True)
        return

    parts = call.data.split("_")
    # get_msgs_{dash_name}_{period}
    period = parts[-1]
    dash_name = "_".join(parts[2:-1])
    
    bot.answer_callback_query(call.id, f"⌛ Fetching {period} messages for {dash_name}...")
    
    # تحديد التاريخ
    target_date = date.today() if period == "today" else date.today() - timedelta(days=1)
    date_str_filter = target_date.strftime("%Y-%m-%d")
    
    all_found_messages = []
    
    # البحث عن اللوحات التي تطابق الاسم
    target_dashboards = [d for d in DASHBOARD_CONFIGS if d["name"] == dash_name]
    
    if not target_dashboards:
        bot.send_message(call.message.chat.id, f"❌ No dashboard found with name: {dash_name}")
        return

    for dash in target_dashboards:
        if not dash.get("is_logged_in"):
            login_for_dashboard(dash)
            dash["is_logged_in"] = True
            
        url = build_ajax_url_for_dashboard(dash)
        j = fetch_ajax_json_for_dashboard(dash, url)
        rows = extract_rows_from_json(j)
        
        if rows:
            for row in rows:
                d_str, num, s_txt, k = row_to_tuple(row)
                if d_str.startswith(date_str_filter):
                    all_found_messages.append((d_str, num, s_txt))
    
    if not all_found_messages:
        bot.send_message(call.message.chat.id, f"📭 No messages found for <b>{dash_name}</b> on {date_str_filter}", parse_mode="HTML")
    else:
        # ترتيب حسب التاريخ تنازلياً
        all_found_messages.sort(key=lambda x: x[0], reverse=True)
        
        # تقسيم الرسائل لرسائل تيليجرام (كل رسالة بحد أقصى 4000 حرف)
        report = f"📋 <b>{dash_name} Messages ({date_str_filter}):</b>\n\n"
        for d_str, num, s_txt in all_found_messages[:30]: # عرض آخر 30 رسالة لتجنب الطول المفرط
            report += f"⏰ {d_str}\n📞 {mask_number(num)}\n💬 {s_txt}\n"
            report += "━━━━━━━━━━━━━━━━━━\n"
            
            if len(report) > 3500:
                bot.send_message(call.message.chat.id, report, parse_mode="HTML")
                report = ""
        
        if report:
            bot.send_message(call.message.chat.id, report, parse_mode="HTML")
    
    show_main_menu(call.message.chat.id)

# ======================
# لوحة التحكم الإدارية
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 Unauthorized!", show_alert=True)
        return
    
    admin_text = format_admin_panel()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btns = [
        types.InlineKeyboardButton("📥 Add Combo", callback_data="admin_add_combo"),
        types.InlineKeyboardButton("🗑️ Delete Combo", callback_data="admin_del_combo"),
        types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton("📄 Full Report", callback_data="admin_full_report"),
        types.InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ Unban User", callback_data="admin_unban"),
        types.InlineKeyboardButton("📢 Broadcast All", callback_data="admin_broadcast_all"),
        types.InlineKeyboardButton("👤 User Info", callback_data="admin_user_info"),
        types.InlineKeyboardButton("🔗 Force Sub", callback_data="admin_force_sub"),
    ]
    
    for i in range(0, len(btns), 2):
        markup.row(*btns[i:i+2])
    
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_main"))
    
    bot.edit_message_text(admin_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

# ======================
# إضافة كومبو جديد مع اسم مخصص
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_add_combo")
def admin_add_combo_step1(call):
    if not is_admin(call.from_user.id):
        return
    
    user_states[call.from_user.id] = "add_combo_name"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    
    bot.edit_message_text(
        "📝 Enter a name for this combo (e.g., 'USA Premium', 'Egypt VIP'):",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_combo_name")
def admin_add_combo_step2(message):
    combo_name = message.text.strip()
    if not combo_name or len(combo_name) < 2:
        bot.reply_to(message, "❌ Combo name must be at least 2 characters!")
        return
    
    user_states[message.from_user.id] = {
        "step": "add_combo_country",
        "combo_name": combo_name
    }
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Cancel", callback_data="admin_panel"))
    
    bot.reply_to(message, f"✅ Combo name saved: {combo_name}\n\n📤 Now send me the TXT file with phone numbers.", reply_markup=markup)

@bot.message_handler(content_types=['document'])
def handle_combo_file(message):
    if not is_admin(message.from_user.id):
        return
    
    state = user_states.get(message.from_user.id)
    if not state or "combo_name" not in state:
        return
    
    combo_name = state["combo_name"]
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8')
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        
        if not lines:
            bot.reply_to(message, "❌ The file is empty!")
            del user_states[message.from_user.id]
            return
        
        first_num = clean_number(lines[0])
        country_code = None
        
        # البحث عن رمز الدولة
        for code in COUNTRY_CODES:
            if first_num.startswith(code):
                country_code = code
                break
        
        if not country_code:
            bot.reply_to(message, "❌ Could not determine country code!")
            del user_states[message.from_user.id]
            return
        
        # حفظ الكومبو
        save_combo(combo_name, country_code, lines)
        
        name, flag, _ = COUNTRY_CODES[country_code]
        
        reply_msg = f"✅ Combo saved successfully!\n\n"
        reply_msg += f"📝 Name: {combo_name}\n"
        reply_msg += f"🌍 Country: {flag} {name}\n"
        reply_msg += f"🔢 Total numbers: {len(lines)}\n"
        reply_msg += f"📞 Example: {lines[0] if len(lines) > 0 else 'N/A'}\n\n"
        reply_msg += f"📊 Combo has been added successfully!"
        
        bot.reply_to(message, reply_msg)
        del user_states[message.from_user.id]
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        del user_states[message.from_user.id]

# ======================
# حذف الكومبو (محسن)
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_del_combo")
def admin_del_combo_list(call):
    if not is_admin(call.from_user.id):
        return
    
    combos = get_all_combos_with_names()
    
    if not combos:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
        bot.edit_message_text("📭 No combos available to delete.", call.message.chat.id, call.message.message_id, reply_markup=markup)
        return
    
    message = "🗑️ Select combo to delete:\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for combo in combos:
        combo_id, combo_name, country_code, _ = combo
        if country_code in COUNTRY_CODES:
            name, flag, _ = COUNTRY_CODES[country_code]
            btn_text = f"{flag} {combo_name or name} ({country_code})"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"del_combo_{combo_id}"))
    
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    
    bot.edit_message_text(message, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_combo_"))
def confirm_del_combo(call):
    if not is_admin(call.from_user.id):
        return
    
    combo_id = int(call.data.split("_", 2)[2])
    combo_data = get_combo_by_id(combo_id)
    
    if not combo_data:
        bot.answer_callback_query(call.id, "❌ Combo not found!", show_alert=True)
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_del_yes_{combo_id}"),
        types.InlineKeyboardButton("❌ No, Cancel", callback_data="admin_del_combo")
    )
    
    name, flag, _ = COUNTRY_CODES.get(combo_data["country_code"], ("Unknown", "🌍", ""))
    
    confirm_msg = f"⚠️ Confirm deletion:\n\n"
    confirm_msg += f"📝 Name: {combo_data['name']}\n"
    confirm_msg += f"🌍 Country: {flag} {name}\n"
    confirm_msg += f"🔢 Numbers: {len(combo_data['numbers'])}\n\n"
    confirm_msg += f"Are you sure you want to delete this combo?"
    
    bot.edit_message_text(confirm_msg, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_del_yes_"))
def execute_del_combo(call):
    if not is_admin(call.from_user.id):
        return
    
    combo_id = int(call.data.split("_", 3)[3])
    combo_data = get_combo_by_id(combo_id)
    
    if not combo_data:
        bot.answer_callback_query(call.id, "❌ Combo not found!", show_alert=True)
        return
    
    deleted = delete_combo_by_id(combo_id)
    
    if deleted:
        name, flag, _ = COUNTRY_CODES.get(combo_data["country_code"], ("Unknown", "🌍", ""))
        reply_msg = f"✅ Combo deleted successfully!\n\n"
        reply_msg += f"📝 Name: {combo_data['name']}\n"
        reply_msg += f"🌍 Country: {flag} {name}\n"
        reply_msg += f"🗑️ Combo has been permanently deleted."
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
        
        bot.edit_message_text(reply_msg, call.message.chat.id, call.message.message_id, reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "❌ Failed to delete combo!", show_alert=True)

# ======================
# بقية دوال الإدارة
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id):
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM users WHERE is_banned = 0")
    active_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM combos")
    total_combos = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM otp_logs")
    otp_count = c.fetchone()[0]
    
    conn.close()
    
    stats_text = "📊 ♛ 𝘾𝙤𝙢𝙢𝙖𝙣𝙙𝙤 𝗢𝗧𝗣 ♛ - Statistics\n\n"
    stats_text += f"👥 Total users: {total_users}\n"
    stats_text += f"✅ Active users: {active_users}\n"
    stats_text += f"🌍 Total combos: {total_combos}\n"
    stats_text += f"🔑 OTPs received: {otp_count}\n"
    stats_text += f"📈 Active rate: {(active_users/total_users*100):.1f}%" if total_users > 0 else "📈 Active rate: 0%"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban")
def admin_ban_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "ban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("🚫 Enter user ID to ban:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "ban_user")
def admin_ban_step2(message):
    try:
        uid = int(message.text)
        ban_user(uid)
        reply_msg = f"✅ User banned successfully!\n\n🆔 User ID: {uid}"
        bot.reply_to(message, reply_msg)
        del user_states[message.from_user.id]
    except:
        bot.reply_to(message, "❌ Invalid user ID!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban")
def admin_unban_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "unban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("✅ Enter user ID to unban:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "unban_user")
def admin_unban_step2(message):
    try:
        uid = int(message.text)
        unban_user(uid)
        reply_msg = f"✅ User unbanned successfully!\n\n🆔 User ID: {uid}"
        bot.reply_to(message, reply_msg)
        del user_states[message.from_user.id]
    except:
        bot.reply_to(message, "❌ Invalid user ID!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_all")
def admin_broadcast_all_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "broadcast_all"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("📢 Send message to broadcast:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_all")
def admin_broadcast_all_step2(message):
    users = get_all_users()
    success = 0
    for uid in users:
        try:
            bot.send_message(uid, message.text)
            success += 1
        except:
            pass
    reply_msg = f"✅ Broadcast completed!\n\n📤 Sent to: {success}/{len(users)}\n📊 Success rate: {(success/len(users)*100):.1f}%"
    bot.reply_to(message, reply_msg)
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_user_info")
def admin_user_info_step1(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "get_user_info"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    bot.edit_message_text("👤 Enter user ID:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "get_user_info")
def admin_user_info_step2(message):
    try:
        uid = int(message.text)
        user = get_user_info(uid)
        if not user:
            bot.reply_to(message, "❌ User not found!")
            return
        status = "🚫 Banned" if user[6] else "✅ Active"
        country_info = COUNTRY_CODES.get(user[4], ("Unknown", "", ""))
        info = "👤 User Information\n\n"
        
        info += f"🆔 User ID: {user[0]}\n"
        info += f"👤 Username: @{user[1] or 'N/A'}\n"
        info += f"👥 Name: {user[2] or ''} {user[3] or ''}\n"
        info += f"🌍 Country: {country_info[0] if country_info[0] else 'Unset'}\n"
        info += f"📱 Assigned number: {user[5] or 'N/A'}\n"
        info += f"📊 Status: {status}\n"
        
        bot.reply_to(message, info)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_full_report")
def admin_full_report(call):
    if not is_admin(call.from_user.id):
        return
    
    try:
        # إنشاء التقرير
        report = "📊 ♛ 𝘾𝙤𝙢𝙢𝙖𝙣𝙙𝙤 𝗢𝗧𝗣 ♛ - Complete Bot Report\n"
        report += "=" * 50 + "\n\n"
        
        # معلومات المستخدمين
        report += "👥 Users Information:\n"
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        
        for user in users:
            status = "Banned" if user[6] else "Active"
            report += f"ID: {user[0]} | @{user[1] or 'N/A'} | Number: {user[5] or 'N/A'} | Status: {status}\n"
        
        report += "\n" + "=" * 50 + "\n\n"
        
        # معلومات الكومبوهات
        report += "🌍 Combos Information:\n"
        c.execute("SELECT combo_name, country_code, numbers FROM combos")
        combos = c.fetchall()
        
        for combo in combos:
            name, country, numbers = combo
            num_list = json.loads(numbers) if numbers else []
            country_name = COUNTRY_CODES.get(country, ("Unknown", "", ""))[0]
            report += f"Name: {name} | Country: {country_name} | Numbers: {len(num_list)}\n"
        
        report += "\n" + "=" * 50 + "\n\n"
        
        # سجل الأكواد
        report += "🔑 Recent OTP Logs:\n"
        c.execute("SELECT * FROM otp_logs ORDER BY timestamp DESC LIMIT 50")
        logs = c.fetchall()
        
        for log in logs:
            report += f"Number: {log[1]} | OTP: {log[2]} | Time: {log[4]}\n"
        
        conn.close()
        
        report += "\n" + "=" * 50 + "\n\n"
        report += f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # حفظ التقرير في ملف
        with open("kavo_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        
        # إرسال الملف
        with open("kavo_report.txt", "rb") as f:
            bot.send_document(
    call.from_user.id,
    f,
    caption="📊 𝘾𝙤𝙢𝙢𝙖𝙣𝙙𝙤 𝗢𝗧𝗣 - Complete Report"
)
        
        # حذف الملف المؤقت
        os.remove("kavo_report.txt")
        
        bot.answer_callback_query(call.id, "✅ Report sent successfully!", show_alert=True)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {e}", show_alert=True)

# ======================
# دوال الاشتراك الإجباري
# ======================
@bot.callback_query_handler(func=lambda call: call.data == "admin_force_sub")
def admin_force_sub_menu(call):
    if not is_admin(call.from_user.id):
        return
    
    channels = get_all_force_sub_channels(enabled_only=False)
    text = "⚙️ Force Sub Channels Management:\n"
    text += f"Total channels: {len(channels)}\n"
    text += "──────────────────\n"
    
    markup = types.InlineKeyboardMarkup()
    
    for ch_id, url, desc in channels:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT enabled FROM force_sub_channels WHERE id=?", (ch_id,))
        enabled = c.fetchone()[0]
        conn.close()
        
        status = "✅" if enabled else "❌"
        btn_text = f"{status} {desc or url[:25]}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"edit_channel_{ch_id}"))
    
    markup.add(types.InlineKeyboardButton("➕ Add Channel", callback_data="add_channel"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_channel")
def add_channel_step1(call):
    if not is_admin(call.from_user.id):
        return
    
    user_states[call.from_user.id] = "add_channel_url"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_force_sub"))
    
    bot.edit_message_text(
        "Send channel link (e.g., https://t.me/xxx or @xxx):",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_channel_url")
def add_channel_step2(message):
    url = message.text.strip()
    if not (url.startswith("@") or url.startswith("https://t.me/")):
        bot.reply_to(message, "❌ Invalid link! Must start with @ or https://t.me/")
        return
    
    user_states[message.from_user.id] = {"step": "add_channel_desc", "url": url}
    bot.reply_to(message, "Enter channel description (or leave empty):")

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), dict) and user_states[msg.from_user.id].get("step") == "add_channel_desc")
def add_channel_step3(message):
    data = user_states[message.from_user.id]
    url = data["url"]
    desc = message.text.strip()
    
    if add_force_sub_channel(url, desc):
        bot.reply_to(message, f"✅ Channel added:\n{url}\nDescription: {desc or '—'}")
    else:
        bot.reply_to(message, "❌ Channel already exists!")
    
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_channel_"))
def edit_channel_menu(call):
    if not is_admin(call.from_user.id):
        return
    
    try:
        ch_id = int(call.data.split("_")[2])
    except:
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_url, description, enabled FROM force_sub_channels WHERE id=?", (ch_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        bot.answer_callback_query(call.id, "❌ Channel not found!", show_alert=True)
        return
    
    url, desc, enabled = row
    status = "Enabled" if enabled else "Disabled"
    
    text = f"🔧 Channel Management:\nURL: {url}\nDescription: {desc or '—'}\nStatus: {status}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ Edit Description", callback_data=f"edit_desc_{ch_id}"))
    
    if enabled:
        markup.add(types.InlineKeyboardButton("❌ Disable", callback_data=f"toggle_channel_{ch_id}"))
    else:
        markup.add(types.InlineKeyboardButton("✅ Enable", callback_data=f"toggle_channel_{ch_id}"))
    
    markup.add(types.InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_channel_{ch_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_force_sub"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_channel_"))
def toggle_channel(call):
    ch_id = int(call.data.split("_")[2])
    toggle_force_sub_channel(ch_id)
    bot.answer_callback_query(call.id, "✅ Channel status updated!", show_alert=True)
    edit_channel_menu(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_channel_"))
def delete_channel(call):
    ch_id = int(call.data.split("_")[2])
    if delete_force_sub_channel(ch_id):
        bot.answer_callback_query(call.id, "✅ Channel deleted!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ Failed to delete!", show_alert=True)
    admin_force_sub_menu(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_desc_"))
def edit_desc_step1(call):
    ch_id = int(call.data.split("_")[2])
    user_states[call.from_user.id] = f"edit_desc_{ch_id}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"edit_channel_{ch_id}"))
    
    bot.edit_message_text(
        "Enter new description:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: isinstance(user_states.get(msg.from_user.id), str) and user_states[msg.from_user.id].startswith("edit_desc_"))
def edit_desc_step2(message):
    try:
        ch_id = int(user_states[message.from_user.id].split("_")[2])
        desc = message.text.strip()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE force_sub_channels SET description = ? WHERE id = ?", (desc, ch_id))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, "✅ Description updated!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")
    
    del user_states[message.from_user.id]

# ======================
# الدوال المساعدة للدول
# ======================
def get_country_info(number):
    if not number:
        return "Unknown", "🌍", "UNKNOWN"
    
    # تطبيع الرقم أولاً
    normalized = normalize_phone_number(number)
    if not normalized:
        return "Unknown", "🌍", "UNKNOWN"
    
    # البحث عن رمز الدولة
    for code, (name, flag, upper_name) in COUNTRY_CODES.items():
        if normalized.startswith(code):
            # إذا كان الرقم يبدأ برمز الدولة مباشرة
            return name, flag, upper_name
    
    # إذا لم يتم العثور، حاول البحث في الأرقام الأصلية
    clean_original = number.strip().replace("+", "").replace(" ", "").replace("-", "")
    for code, (name, flag, upper_name) in COUNTRY_CODES.items():
        if clean_original.startswith(code):
            return name, flag, upper_name
    
    return "Unknown", "🌍", "UNKNOWN"

# ======================
# دالة جديدة: جلب الأرقام المتاحة (غير المستخدمة)
# ======================
def get_available_numbers(country_code, user_id=None):
    """جلب الأرقام المتاحة (غير المستخدمة)"""
    # الحصول على الكومبوهات المناسبة
    all_numbers = get_combo(country_code, user_id)
    
    if not all_numbers:
        print(f"⚠️ لا توجد كومبوهات متاحة للدولة {country_code}")
        return []
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
    used_raw_numbers = [row[0] for row in c.fetchall()]
    conn.close()
    
    # تطبيع الأرقام المستخدمة للمقارنة الصحيحة
    used_numbers = set()
    for num in used_raw_numbers:
        if num:
            normalized = normalize_phone_number(num)
            if normalized:
                used_numbers.add(normalized)
    
    print(f"📊 كومبوهات متاحة: {len(all_numbers)} رقم")
    print(f"📊 أرقام مستخدمة: {len(used_numbers)} رقم")
    
    available = []
    for num in all_numbers:
        normalized_num = normalize_phone_number(num)
        if normalized_num and normalized_num not in used_numbers:
            available.append(num)
    
    print(f"✅ أرقام متاحة فعلياً: {len(available)} رقم")
    return available

# ======================
# الدالة المحسنة لإرسال OTP للمستخدم + الجروب
# ======================
def send_otp_to_user_and_group(date_str, number, sms):
    print(f"\n🎯 بدء إرسال OTP للرقم: {number}")
    print(f"📅 التاريخ: {date_str}")
    
    # مراقبة الأرقام المخزنة
    total_users = debug_user_numbers()
    print(f"📊 إجمالي المستخدمين المخزنين: {total_users}")
    
    otp_code = extract_otp(sms)
    print(f"🔍 OTP المستخرج: {otp_code}")
    
    user_id = get_user_by_number(number)
    print(f"👤 المستخدم المخصص للرقم: {user_id}")
    
    log_otp(number, otp_code, sms, user_id)
    print(f"📝 تم تسجيل OTP في قاعدة البيانات")
    
    # إرسال للمستخدم في الخاص
    user_sent = False
    user_error = None
    
    if user_id:
        try:
            user_message = format_message_for_user(date_str, number, sms)
            
            print(f"📤 محاولة إرسال OTP إلى user_id: {user_id}")
            bot.send_message(user_id, user_message, parse_mode="Markdown")
            user_sent = True
            print(f"✅ تم إرسال OTP للمستخدم {user_id}")
            
        except Exception as e:
            user_error = str(e)
            print(f"❌ فشل إرسال OTP للمستخدم {user_id}: {type(e).__name__} - {user_error}")
            
            # محاولة إعادة إرسال بدون تنسيق إذا كان هناك خطأ
            try:
                simple_msg = f"🔐 Your OTP Code:\n\n📞 Number: {number}\n🔑 OTP: {otp_code}\n⏰ Time: {date_str}"
                bot.send_message(user_id, simple_msg)
                user_sent = True
                print(f"✅ تم إرسال رسالة بسيطة للمستخدم {user_id}")
            except Exception as e2:
                print(f"❌ فشل إرسال الرسالة البسيطة أيضًا: {e2}")
    else:
        print(f"⚠️ لا يوجد مستخدم مخصص لهذا الرقم: {number}")
    
    # إرسال للقناة
    channel_message = format_message_for_channel(date_str, number, sms)
    print(f"📝 تم تنسيق الرسالة للقناة ({len(channel_message)} حرف)")
    
    print(f"📤 إرسال الرسالة إلى القناة...")
    channel_result = send_to_telegram_group(channel_message, otp_code)
    
    if channel_result:
        print(f"✅ تم إرسال الرسالة إلى القناة بنجاح!")
    else:
        print(f"❌ فشل إرسال الرسالة إلى القناة!")
    
    # تسجيل النتائج النهائية
    print(f"📊 نتائج الإرسال:")
    print(f"   - للمستخدم: {'✅ ناجح' if user_sent else '❌ فاشل'}")
    print(f"   - للقناة: {'✅ ناجح' if channel_result else '❌ فاشل'}")
    
    return {
        "user_sent": user_sent,
        "channel_sent": channel_result,
        "user_id": user_id,
        "otp_code": otp_code,
        "user_error": user_error
    }

# ======================
# دوال الاتصال بالـ Dashboard
# ======================
def retry_request(func, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY):
    for attempt in range(max_retries):
        try:
            return func()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                print(f"⚠️  محاولة {attempt + 1}/{max_retries} فشلت: {type(e).__name__}")
                time.sleep(retry_delay)
            else:
                print(f"❌ جميع المحاولات ({max_retries}) فشلت")
                raise
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            raise

def login_for_dashboard(dash):
    print(f"[{dash['name']}] 🔐 محاولة تسجيل الدخول...")
    
    try:
        resp = dash["session"].get(dash["login_page_url"], timeout=TIMEOUT)
        
        # البحث عن الكابتشا بنمطين مختلفين
        match = re.search(r'What is (\d+)\s*\+\s*(\d+)', resp.text)
        if not match:
            match = re.search(r'(\d+)\s*\+\s*(\d+)\s*=\s*\?', resp.text)
            
        if not match:
            print(f"[{dash['name']}] ❌ لم يتم العثور على captcha")
            # طباعة جزء من الصفحة للمساعدة في التشخيص إذا فشل البحث مستقبلاً
            # print(resp.text[:500]) 
            return False
        
        num1, num2 = int(match.group(1)), int(match.group(2))
        captcha_answer = num1 + num2
        print(f"[{dash['name']}] 🔢 Captcha: {num1} + {num2} = {captcha_answer}")

        payload = {
            "username": dash["username"],
            "password": dash["password"],
            "capt": str(captcha_answer)
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": dash["login_page_url"],
        }

        resp = dash["session"].post(dash["login_post_url"], data=payload, headers=headers, timeout=TIMEOUT)
        
        if "dashboard" in resp.text.lower() or "logout" in resp.text.lower() or "/ints/agent" in resp.url:
            print(f"[{dash['name']}] ✅ تسجيل الدخول نجح")
            
            try:
                report_page = dash["base"] + dash.get("stats_page", "/ints/agent/SMSCDRReports")
                r_report = dash["session"].get(report_page, timeout=TIMEOUT)
                
                # تحسين استخراج sesskey
                match_key = re.search(r'sesskey\s*=\s*\"([^\"]+)\"', r_report.text)
                if not match_key:
                    match_key = re.search(r'name=\"sesskey\"\s+value=\"([^\"]+)\"', r_report.text)
                if not match_key:
                    match_key = re.search(r'sesskey=([a-zA-Z0-9+/=]+)', r_report.text)
                
                if match_key:
                    dash["sesskey"] = match_key.group(1)
                    print(f"[{dash['name']}] 🔑 Sesskey: {dash['sesskey'][:10]}...")
                else:
                    dash["sesskey"] = ""
                    print(f"[{dash['name']}] ⚠️ لم يتم العثور على sesskey")
            except Exception as e:
                print(f"[{dash['name']}] ⚠️ خطأ في استخراج sesskey: {e}")
                dash["sesskey"] = ""
            
            return True
        else:
            print(f"[{dash['name']}] ❌ فشل تسجيل الدخول")
            # print(f"DEBUG: {resp.text[:500]}") # لمعرفة سبب الفشل من الموقع
            return False
            
    except Exception as e:
        print(f"[{dash['name']}] ❌ خطأ في تسجيل الدخول: {e}")
        return False

def build_ajax_url_for_dashboard(dash):
    start_date = date.today() - timedelta(days=3650)
    end_date = date.today() + timedelta(days=1)

    fdate1 = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
    fdate2 = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"

    sesskey = dash.get("sesskey", "")
    # تخصيص البارامترات بناءً على نوع اللوحة
    if "85.195.94.50" in dash["base"]:
        q = (
            f"fdate1={quote_plus(fdate1)}&fdate2={quote_plus(fdate2)}&ftermination=&fnum=&fcli=&fgdate=0&fgtermination=0&fgnumber=0&fgcli=0&fg=0"
            f"&sEcho=1&iColumns=8&sColumns=%2C%2C%2C%2C%2C%2C%2C&iDisplayStart=0&iDisplayLength=5000"
            f"&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&mDataProp_4=4&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7"
            f"&sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1&_={int(time.time()*1000)}"
        )
    else:
        q = (
            f"fdate1={quote_plus(fdate1)}&fdate2={quote_plus(fdate2)}&frange=&fclient=&fnum=&fcli=&fgdate=&fgmonth=&fgrange="
            f"&fgclient=&fgnumber=&fgcli=&fg=0&sEcho=1&iColumns=9&sColumns=%2C%2C%2C%2C%2C%2C%2C%2C&iDisplayStart=0&iDisplayLength=5000"
            f"&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&mDataProp_4=4&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7&mDataProp_8=8"
            f"&sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1&sesskey={quote_plus(sesskey)}&_={int(time.time()*1000)}"
        )
    return dash["ajax_url"] + "?" + q

def fetch_ajax_json_for_dashboard(dash, url):
    try:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": dash["base"] + dash.get("stats_page", "/ints/agent/SMSCDRReports"),
        }
        dash["session"].headers.update(headers)
        
        r = dash["session"].get(url, timeout=TIMEOUT)
        
        if r.status_code == 403 or ("login" in r.text.lower() and "login" in r.url.lower()):
            raise Exception("Session expired")
        
        r.raise_for_status()
        
        try:
            return r.json()
        except json.JSONDecodeError:
            raise Exception("Invalid JSON or redirected to login")
            
    except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
        print(f"[{dash['name']}] 🌐 خطأ في الاتصال (Connection Error): {e}")
        dash["is_logged_in"] = False
        return None
    except Exception as e:
        if "Session expired" in str(e):
            print(f"[{dash['name']}] ⏳ الجلسة منتهية. إعادة تسجيل الدخول...")
            if login_for_dashboard(dash):
                return fetch_ajax_json_for_dashboard(dash, url)
            else:
                dash["is_logged_in"] = False
                return None
        else:
            print(f"[{dash['name']}] ❌ خطأ في الجلب: {e}")
            return None

def extract_rows_from_json(j):
    if j is None:
        return []
    
    for key in ("data", "aaData", "rows", "aa_data"):
        if isinstance(j, dict) and key in j:
            return j[key]
    
    if isinstance(j, list):
        return j
    
    if isinstance(j, dict):
        for v in j.values():
            if isinstance(v, list):
                return v
    
    return []

def clean_html(text):
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.strip()
    return text

def clean_number(number):
    if not number:
        return ""
    number = re.sub(r'\D', '', str(number))
    return number

def row_to_tuple(row):
    date_str = ""
    number_str = ""
    sms_str = ""
    
    if isinstance(row, (list, tuple)):
        if len(row) > IDX_DATE:
            date_str = clean_html(row[IDX_DATE])
        if len(row) > IDX_NUMBER:
            number_str = clean_number(row[IDX_NUMBER])
        
        # تحسين استخراج نص الرسالة
        # أحياناً يكون النص في العمود 5، وأحياناً في أعمدة أخرى حسب اللوحة
        possible_sms_indices = [7, 5, 4, 6, 3] # ترتيب الأعمدة المحتملة لنص الرسالة
        for idx in possible_sms_indices:
            if len(row) > idx:
                val = clean_html(row[idx])
                if val and val != "$" and len(val) > 3:
                    sms_str = val
                    break
        
        # إذا لم يجد نصاً صالحاً، نأخذ القيمة الافتراضية حتى لو كانت $
        if not sms_str and len(row) > IDX_SMS:
            sms_str = clean_html(row[IDX_SMS])
    
    unique_key = f"{date_str}|{number_str}|{sms_str}"
    return date_str, number_str, sms_str, unique_key

# ======================
# الحلقة الرئيسية المحسنة
# ======================
def main_loop():
    global REFRESH_INTERVAL
    
    sent_messages = set()
    last_times = {dash["name"]: None for dash in DASHBOARD_CONFIGS}
    
    last_success_time = time.time()
    sms_count = 0

    print("\n" + "=" * 60)
    print("🚀 ♛ 𝘾𝙤𝙢𝙢𝙖𝙣𝙙𝙤 𝗢𝗧𝗣 ♛ - Monitoring Started")
    print("=" * 60)

    print(f"\n🔐 تسجيل الدخول للوحات...")
    for dash in DASHBOARD_CONFIGS:
        retry_count = 0
        max_login_retries = 3
        
        while retry_count < max_login_retries and not dash["is_logged_in"]:
            if login_for_dashboard(dash):
                dash["is_logged_in"] = True
                print(f"[{dash['name']}] ✅ تسجيل الدخول نجح")
            else:
                retry_count += 1
                print(f"[{dash['name']}] ⚠️ محاولة تسجيل الدخول {retry_count}/{max_login_retries} فشلت")
                if retry_count < max_login_retries:
                    time.sleep(5)
        
        if not dash["is_logged_in"]:
            print(f"[{dash['name']}] ❌ فشل تسجيل الدخول بعد {max_login_retries} محاولات")

    print(f"\n🔍 جلب آخر رسالة من كل لوحة...")
    for dash in DASHBOARD_CONFIGS:
        if not dash["is_logged_in"]:
            print(f"[{dash['name']}] ⚠️ تخطي اللوحة (غير مسجل دخول)")
            continue
            
        try:
            url = build_ajax_url_for_dashboard(dash)
            j = fetch_ajax_json_for_dashboard(dash, url)
            rows = extract_rows_from_json(j)
            
            if rows:
                valid_rows = []
                for row in rows:
                    if not (isinstance(row, list) and len(row) > 3): continue
                    d_v, n_v, s_v, _ = row_to_tuple(row)
                    if d_v and '-' in d_v and ':' in d_v and n_v and len(n_v) >= 10 and s_v and len(s_v) > 5:
                        valid_rows.append(row)
                
                if valid_rows:
                    def get_datetime(row):
                        try:
                            return datetime.strptime(clean_html(row[IDX_DATE]), "%Y-%m-%d %H:%M:%S")
                        except:
                            return datetime.min
                    
                    valid_rows.sort(key=get_datetime, reverse=True)
                    
                    # معالجة كافة الرسائل الجديدة في الجلب الأولي
                    new_found_initial = False
                    for row in valid_rows:
                        d_str, num, s_txt, k = row_to_tuple(row)
                        if k not in sent_messages:
                            if not new_found_initial:
                                print(f"[{dash['name']}] 🚨 جلب الرسائل الجديدة الأولية...")
                                new_found_initial = True
                            
                            print(f"[{dash['name']}] ✅ رسالة: {mask_number(num)} في {d_str}")
                            send_otp_to_user_and_group(d_str, num, s_txt)
                            sent_messages.add(k)
                            
                            if last_times[dash["name"]] is None or d_str > last_times[dash["name"]]:
                                last_times[dash["name"]] = d_str
                                
                            sms_count += 1
                            last_success_time = time.time()
                    
                    if not new_found_initial and valid_rows:
                        latest_row = valid_rows[0]
                        d_str, num, s_txt, k = row_to_tuple(latest_row)
                        print(f"[{dash['name']}] ✅ آخر رسالة موجودة مسبقاً: {mask_number(num)} في {d_str}")
                        last_times[dash["name"]] = d_str
        except Exception as e:
            print(f"[{dash['name']}] ⚠️ خطأ في الجلب الأولي: {e}")

    print(f"\n✅ بدء المراقبة المستمرة (كل {REFRESH_INTERVAL} ثوانٍ)...")
    print(f"📊 إجمالي الرسائل حتى الآن: {sms_count}")
    print("=" * 60)

    dash_cycle = itertools.cycle(DASHBOARD_CONFIGS)
    consecutive_errors = {dash["name"]: 0 for dash in DASHBOARD_CONFIGS}
    max_consecutive_errors = 10

    while True:
        dash = next(dash_cycle)
        
        try:
            print(f"\n[{dash['name']}] ⏱️ دورة المراقبة #{sms_count + 1}")
            
            if not dash["is_logged_in"]:
                print(f"[{dash['name']}] 🔁 محاولة إعادة تسجيل الدخول...")
                if login_for_dashboard(dash):
                    dash["is_logged_in"] = True
                else:
                    print(f"[{dash['name']}] ❌ فشل إعادة تسجيل الدخول")
                    time.sleep(REFRESH_INTERVAL)
                    continue

            url = build_ajax_url_for_dashboard(dash)
            j = fetch_ajax_json_for_dashboard(dash, url)
            
            if j is None:
                print(f"[{dash['name']}] ❌ لا توجد بيانات")
                dash["is_logged_in"] = False
                continue
                
            rows = extract_rows_from_json(j)

            if rows:
                valid_rows = []
                for row in rows:
                    if not (isinstance(row, list) and len(row) > 3): continue
                    d_v, n_v, s_v, _ = row_to_tuple(row)
                    if d_v and '-' in d_v and ':' in d_v and n_v and len(n_v) >= 10 and s_v and len(s_v) > 5:
                        valid_rows.append(row)

                if valid_rows:
                    def get_datetime(row):
                        try:
                            return datetime.strptime(clean_html(row[IDX_DATE]), "%Y-%m-%d %H:%M:%S")
                        except:
                            return datetime.min
                    
                    valid_rows.sort(key=get_datetime, reverse=True)
                    latest_row = valid_rows[0]
                    date_str, number, sms, key = row_to_tuple(latest_row)

                    # جلب جميع الرسائل الجديدة وإرسالها للقناة
                    new_found = False
                    for row in valid_rows:
                        d_str, num, s_txt, k = row_to_tuple(row)
                        if (last_times[dash["name"]] is None or d_str > last_times[dash["name"]]) and k not in sent_messages:
                            if not new_found:
                                print(f"\n[{dash['name']}] 🚨 🆕 رسائل جديدة!")
                                new_found = True
                            
                            print(f"📞 الرقم: {mask_number(num)} | 📅 التاريخ: {d_str}")
                            send_otp_to_user_and_group(d_str, num, s_txt)
                            
                            sent_messages.add(k)
                            # تحديث last_times بأحدث تاريخ تم إرساله
                            if last_times[dash["name"]] is None or d_str > last_times[dash["name"]]:
                                last_times[dash["name"]] = d_str
                            
                            sms_count += 1
                            last_success_time = time.time()
                    
                    if new_found:
                        consecutive_errors[dash["name"]] = 0
                        print(f"📊 إجمالي الرسائل: {sms_count}")
                    else:
                        print(f"[{dash['name']}] ✓ فحص {len(rows)} رسالة - لا يوجد جديد")
                else:
                    print(f"[{dash['name']}] [=] لا رسائل صالحة من أصل {len(rows)} رسالة")
            else:
                print(f"[{dash['name']}] [=] لا بيانات")

            if len(sent_messages) > 1000:
                sent_messages = set(list(sent_messages)[-1000:])
                print(f"🧹 تنظيف الذاكرة - حفظ آخر 1000 رسالة فقط")

            consecutive_errors[dash["name"]] = 0

        except KeyboardInterrupt:
            print("\n⛔ توقف يدوي")
            break
            
        except Exception as e:
            consecutive_errors[dash["name"]] += 1
            print(f"[{dash['name']}] ❌ خطأ ({consecutive_errors[dash['name']]}/{max_consecutive_errors}): {e}")
            
            if consecutive_errors[dash["name"]] >= max_consecutive_errors:
                print(f"[{dash['name']}] ⚠️ إعادة تسجيل الدخول بعد {max_consecutive_errors} أخطاء")
                dash["is_logged_in"] = False
                consecutive_errors[dash["name"]] = 0

        time.sleep(REFRESH_INTERVAL)

# ======================
# تشغيل البوت التفاعلي
def run_bot():
    print("\n🤖 Starting 𝘾𝙤𝙢𝙢𝙖𝙣𝙙𝙤 𝗢𝗧𝗣 Bot...")
    
    while True:
        try:
            bot.polling(none_stop=True, timeout=30, long_polling_timeout=30, skip_pending=True)
            
        except Exception as e:
            print(f"🚨 خطأ في البوت التفاعلي: {type(e).__name__} - {str(e)}")
            print("⏳ إعادة تشغيل البوت بعد 5 ثواني...")
            time.sleep(5)

# ======================
# التشغيل الرئيسي
# ======================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("        ♛ 𝘾𝙤𝙢𝙢𝙖𝙣𝙙𝙤 𝗢𝗧𝗣 ♛ 🛜 𝗕𝗢𝗧")
    print("=" * 60)
    
    # دالة لتصحيح تنسيق الأرقام في قاعدة البيانات
    def fix_number_formatting():
        """تصحيح تنسيق الأرقام في قاعدة البيانات"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id, assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
        users = c.fetchall()
        
        fixed_count = 0
        for user_id, number in users:
            normalized = normalize_phone_number(number)
            if normalized != number:
                c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (normalized, user_id))
                print(f"📝 تصحيح الرقم للمستخدم {user_id}: {number} → {normalized}")
                fixed_count += 1
        
        conn.commit()
        conn.close()
        print(f"✅ تم تصحيح {fixed_count} رقم")
        
        return fixed_count
    
    # استدعاء init_db مباشرة
    init_db()
    
    # تصحيح تنسيق الأرقام قبل التشغيل
    print("\n🛠️ تصحيح تنسيق الأرقام في قاعدة البيانات...")
    fixed = fix_number_formatting()
    print(f"✅ تم تصحيح {fixed} رقم")
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n👋 ♛ إيقاف 𝘾𝙤𝙢𝙢𝙖𝙣𝙙𝙤 𝗢𝗧𝗣 ♛")

# =========================================================
# ADDITIONS ONLY - AUTO ADDED (NO ORIGINAL CODE MODIFIED)
# =========================================================

def fetch_sesskey(dash):
    try:
        url = dash["base"] + dash["stats_page"]
        r = dash["session"].get(url, timeout=20)

        m = re.search(r'sesskey\s*=\s*\"([^\"]+)\"', r.text)
        if not m:
            m = re.search(r'name=\"sesskey\"\s+value=\"([^\"]+)\"', r.text)

        if m:
            dash["sesskey"] = m.group(1)
            print(f"[{dash['name']}] sesskey OK")
            return True
        else:
            print(f"[{dash['name']}] sesskey NOT FOUND")
            return False
    except Exception as e:
        print(f"[{dash['name']}] sesskey ERROR: {e}")
        return False
