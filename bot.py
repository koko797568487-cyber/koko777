import threading
import time
import requests
import json
import random

from config import (
    BOT_TOKEN, TELEGRAM_API, user_sessions, session_lock,
    get_default_session, GAME_TYPES, DEFAULT_GAME_TYPE
)
from core import (
    LotteryAPI, SigmaStrategyEngine, SmartTrendReversalEngine,
    PatternHunterEngine, AILogicTrendStrategyEngine, MartingaleStrategyEngine,
    FibonacciStrategyEngine, ParoliStrategyEngine, DAlembertStrategyEngine,
    TrendFollowingStrategyEngine, OscillatorStrategyEngine,
    MomentumStrategyEngine, MeanReversionStrategyEngine
)

# ==================== UI FORMATTERS ====================
def clean_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def send_message(chat_id, html_text, reply_markup=None):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": html_text, "parse_mode": "HTML"}
    if reply_markup: payload["reply_markup"] = json.dumps(reply_markup)
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def send_beautiful_dashboard(chat_id, sess):
    api = sess.get('api')
    if sess.get('virtual_mode', False):
        bal = sess.get('virtual_balance', 10000.0)
        mode = "🧪 VIRTUAL SIMULATOR"
        acc_id = "VIRTUAL_USER_99"
    else:
        bal = api.get_balance() if api else -1.0
        if bal < 0: bal = sess.get('last_known_balance', 0.0)
        else: sess['last_known_balance'] = bal
        mode = "💰 REAL INTEL VAULT"
        acc_id = api.user_id if api else "Unknown"

    game_name = GAME_TYPES.get(sess.get('game_key', DEFAULT_GAME_TYPE), GAME_TYPES["1"])['name']
    strat_mode = sess.get('strategy_mode', 'SIGMA')
    strat_names = {
        'SIGMA': "🔮 Sigma Weighted Core",
        'BS_ORDER': f"📜 Custom Pattern ({''.join(sess.get('bs_custom_sequence', ['B','S']))})",
        'TREND_REVERSAL': "🔄 Smart Trend & Reversal",
        'PATTERN_HUNTER': "🎯 Pattern Hunter Engine",
        'AI_TREND_LOGIC': "🧠 AI Trend Logic",
        'MARTINGALE': "📈 Martingale",
        'FIBONACCI': "🔢 Fibonacci",
        'PAROLI': "🍀 Paroli",
        'DALEMBERT': "⚖️ D'Alembert",
        'TREND_FOLLOWING': "📊 Trend Following",
        'OSCILLATOR': "📊 Oscillator",
        'MOMENTUM': "🚀 Momentum",
        'MEAN_REVERSION': "🔄 Mean Reversion"
    }
    strat_name = strat_names.get(strat_mode, "⚙️ Adaptive Core")

    sigma_idx = sess.get('last_sigma_index', "--")
    stability = sess.get('last_stability', "--")
    status_str = "🟢 ACTIVE / RUNNING" if sess.get('is_running') else "🔴 STANDBY / LOCKED"

    dashboard = f"""
<blockquote>
<b>⚡🌟 [ SIGMA NEXUS v5 ] 🌟⚡</b>
<b>━━━━━━━ ⚙️ STATUS ⚙️ ━━━━━━━</b>
<b>👤 USER NODE ID :</b> {clean_html(acc_id)}
<b>⚙️ ENGINE MODE :</b> {clean_html(mode)}
<b>🔮 STRATEGY    :</b> {clean_html(strat_name)}
<b>🎮 GAME ROOM   :</b> {clean_html(game_name)}
<b>━━━━━━━ 📊 METRICS 📊 ━━━━━━━</b>
<b>📊 SIGMA INDEX :</b> {sigma_idx}
<b>🔥 STABILITY   :</b> {stability}%
<b>━━━━━━━ 💰 WALLET 💰 ━━━━━━━</b>
<b>💳 LIVE WALLET :</b> {bal:.2f} Ks
<b>💵 BASE UNIT   :</b> {sess.get('base_amount')} Ks
<b>🧧 TAKE PROFIT :</b> {sess.get('profit_target'):.2f} Ks
<b>🛑 STOP LOSS   :</b> {sess.get('stop_loss'):.2f} Ks
<b>📈 METRIC P/L  :</b> {sess.get('total_profit'):.2f} Ks
<b>━━━━━━━ ⚡ POWER ⚡ ━━━━━━━</b>
<b>⚡ ENGINE POWER :</b> <b>{status_str}</b>
</blockquote>"""
    send_message(chat_id, dashboard)

def send_bet_quote(chat_id, lines_list):
    inner = "\n".join([f"<b>{clean_html(line)}</b>" if line.strip() else "" for line in lines_list])
    send_message(chat_id, f"<blockquote>{inner}</blockquote>")

def send_test_styled_message(chat_id):
    test_msg = """
<blockquote>
<b>🌟 [ TEST STYLED MESSAGE ] 🌟</b>
<b>━━━━━━━━━━━━━━━━━━━━</b>
<i>This is a sample message with rich formatting.</i>
<b>• Bold</b>, <i>italic</i>, <u>underline</u>
<code>inline code</code>
<pre>preformatted block</pre>
<b>━━━━━━━━━━━━━━━━━━━━</b>
🎯 <b>Prediction:</b> <b>BIG</b> with 87% confidence
💰 <b>Amount:</b> 100 Ks
⏳ <b>Period:</b> #123456
</blockquote>
    """
    send_message(chat_id, test_msg)

# ==================== KEYBOARDS ====================
def get_login_keyboard():
    return {"keyboard": [[{"text": "🔑 Secure Account Login"}]], "resize_keyboard": True}

def get_main_keyboard():
    return {"keyboard": [
        [{"text": "⚙️ Bet Settings"}, {"text": "🎯 Target Settings"}],
        [{"text": "🔮 Strategy Menu"}, {"text": "🔄 Virtual Switch"}],
        [{"text": "📊 Check Info Dashboard"}, {"text": "📨 Test Styled Message"}],
        [{"text": "▶️ Start Engine"}, {"text": "⏹️ Stop Engine"}],
        [{"text": "🚪 Secure Logout"}]
    ], "resize_keyboard": True}

def get_bet_settings_keyboard():
    return {"keyboard": [
        [{"text": "💵 Set Base Amount"}, {"text": "📊 Set Multiplier Sequence"}],
        [{"text": "🎮 Select Game Type"}, {"text": "💸 Set Virtual Balance"}],
        [{"text": "◀️ Main Menu"}]
    ], "resize_keyboard": True}

def get_target_settings_keyboard():
    return {"keyboard": [
        [{"text": "🧧 Set Profit Target"}, {"text": "🛑 Set Stop Loss"}],
        [{"text": "◀️ Main Menu"}]
    ], "resize_keyboard": True}

def get_strategy_menu_keyboard():
    return {"keyboard": [
        [{"text": "⚡ Sigma Trend Core"}, {"text": "🎯 Pattern Hunter Engine"}],
        [{"text": "🔄 Smart Trend & Reversal"}, {"text": "🧠 AI Trend Logic"}],
        [{"text": "📈 Martingale"}, {"text": "🔢 Fibonacci"}],
        [{"text": "🍀 Paroli"}, {"text": "⚖️ D'Alembert"}],
        [{"text": "📊 Trend Following"}, {"text": "📊 Oscillator"}],
        [{"text": "🚀 Momentum"}, {"text": "🔄 Mean Reversion"}],
        [{"text": "📜 Custom BS Order Pattern"}],
        [{"text": "📝 Set Custom BS Order"}, {"text": "◀️ Main Menu"}]
    ], "resize_keyboard": True}

def get_game_type_keyboard():
    buttons = [[{"text": gt["name"]}] for gt in GAME_TYPES.values()]
    buttons.append([{"text": "◀️ Main Menu"}])
    return {"keyboard": buttons, "resize_keyboard": True}

# ==================== BETTING ENGINE ====================
def betting_loop(user_id, chat_id):
    while True:
        with session_lock:
            sess = user_sessions.get(user_id)
            if not sess or not sess.get('is_running'): break

            api = sess['api']
            current_p_l = sess['total_profit']
            stop_loss = sess['stop_loss']
            profit_target = sess['profit_target']
            game_key = sess.get('game_key', DEFAULT_GAME_TYPE)
            base_amt = sess.get('base_amount', 10)
            step = sess['current_step']
            seq = sess['betting_sequence']
            strat_mode = sess.get('strategy_mode', 'SIGMA')
            virtual_mode = sess.get('virtual_mode', False)
            virtual_balance = sess.get('virtual_balance', 0.0)
            last_known_bal = sess.get('last_known_balance', 0.0)

        sigma_engine = SigmaStrategyEngine()
        trend_engine = SmartTrendReversalEngine()
        hunter_engine = PatternHunterEngine()
        ai_trend_engine = AILogicTrendStrategyEngine()
        martingale_engine = MartingaleStrategyEngine()
        fibonacci_engine = FibonacciStrategyEngine()
        paroli_engine = ParoliStrategyEngine()
        dalembert_engine = DAlembertStrategyEngine()
        trend_following_engine = TrendFollowingStrategyEngine()
        oscillator_engine = OscillatorStrategyEngine()
        momentum_engine = MomentumStrategyEngine()
        mean_reversion_engine = MeanReversionStrategyEngine()

        game_type = GAME_TYPES.get(game_key, GAME_TYPES["1"])
        game_type_id = game_type['typeId']
        is_trx = game_type['is_trx']

        if stop_loss > 0 and current_p_l <= -abs(stop_loss):
            send_message(chat_id, "<b>🚨 [STOP LOSS] Triggered Security Shutdown.</b>")
            break
        if profit_target > 0 and current_p_l >= profit_target:
            send_message(chat_id, "<b>🏆 [TARGET ACHIEVED] Automation Success.</b>")
            break

        issue = api.get_current_issue(game_type_id) if api else str(int(time.time()) // 30)
        if not issue:
            time.sleep(2)
            continue

        numbers_all = []
        if api:
            recents = api.get_recent_results(20, game_type_id, is_trx)
            if recents:
                numbers_all = [int(r.get('number', 0)) for r in recents]

        if not numbers_all:
            numbers_all = [random.randint(0, 9) for _ in range(20)]

        if strat_mode == 'SIGMA':
            sigma_idx, size_pred = sigma_engine.compute_sigma_prediction(numbers_all)
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            strat_desc = f"Sigma Index {sigma_idx} (Stab {stability_score}%)"
        elif strat_mode == 'TREND_REVERSAL':
            sigma_idx, size_pred, desc = trend_engine.predict(numbers_all)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            strat_desc = desc
        elif strat_mode == 'PATTERN_HUNTER':
            sigma_idx, size_pred, desc = hunter_engine.predict(numbers_all)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            strat_desc = desc
        elif strat_mode == 'AI_TREND_LOGIC':
            sigma_idx, size_pred, desc = ai_trend_engine.predict(numbers_all)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            strat_desc = desc
        elif strat_mode == 'MARTINGALE':
            sigma_idx, size_pred, desc = martingale_engine.predict(numbers_all, step)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            strat_desc = desc
        elif strat_mode == 'FIBONACCI':
            sigma_idx, size_pred, desc = fibonacci_engine.predict(numbers_all, step)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            strat_desc = desc
        elif strat_mode == 'PAROLI':
            sigma_idx, size_pred, desc = paroli_engine.predict(numbers_all, True)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            strat_desc = desc
        elif strat_mode == 'DALEMBERT':
            sigma_idx, size_pred, desc = dalembert_engine.predict(numbers_all)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            strat_desc = desc
        elif strat_mode == 'TREND_FOLLOWING':
            sigma_idx, size_pred, desc = trend_following_engine.predict(numbers_all)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            strat_desc = desc
        elif strat_mode == 'OSCILLATOR':
            sigma_idx, size_pred, desc = oscillator_engine.predict(numbers_all)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            strat_desc = desc
        elif strat_mode == 'MOMENTUM':
            sigma_idx, size_pred, desc = momentum_engine.predict(numbers_all)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            strat_desc = desc
        elif strat_mode == 'MEAN_REVERSION':
            sigma_idx, size_pred, desc = mean_reversion_engine.predict(numbers_all)
            pred_char = 'B' if size_pred == "BIG" else 'S'
            stability_score = sigma_engine.get_sigma_stability(numbers_all)
            strat_desc = desc
        elif strat_mode == 'BS_ORDER':
            with session_lock:
                idx = sess.get('bs_custom_index', 0)
                seq_list = sess.get('bs_custom_sequence', ['B', 'S'])
                pred_char = seq_list[idx]
                sess['bs_custom_index'] = (idx + 1) % len(seq_list)
            sigma_idx = "--"
            stability_score = "--"
            strat_desc = f"Custom Pattern [{' '.join(seq_list)}]"
        else:
            pred_char = random.choice(['B', 'S'])
            sigma_idx = "--"
            stability_score = "--"
            strat_desc = "Random fallback"

        with session_lock:
            sess['last_sigma_index'] = sigma_idx
            sess['last_stability'] = stability_score

        bet_side_text = "BIG" if pred_char == 'B' else "SMALL"
        if step >= len(seq): step = 0
        bet_count = seq[step]
        total_amount = base_amt * bet_count
        mode_header = "🧪 VIRTUAL GRID SIMULATION" if virtual_mode else "💰 INTEL VAULT REAL INVESTMENT"

        if virtual_mode:
            if total_amount > virtual_balance:
                send_message(chat_id, "<b>❌ Virtual balance insufficient!</b>")
                break
            send_bet_quote(chat_id, [mode_header, f"🎯 TARGET ANOMALY: {bet_side_text} {total_amount:.2f} Ks", f"📊 STRATEGY: {strat_desc}", f"⏳ PERIOD: {issue}"])
        else:
            server_bal = api.get_balance() if api else -1.0
            if server_bal < 0: server_bal = last_known_bal
            if total_amount > server_bal:
                send_message(chat_id, "<b>❌ Wallet balance insufficient! Loop stopped.</b>")
                break
            bet_type = 13 if pred_char == 'B' else 14
            ok, msg, _ = api.place_bet(issue, base_amt, bet_count, bet_type, game_type_id)
            if not ok:
                time.sleep(2)
                continue
            send_bet_quote(chat_id, [mode_header, f"🎯 TARGET ANOMALY: {bet_side_text} {total_amount:.2f} Ks", f"📊 STRATEGY: {strat_desc}", f"⏳ PERIOD: {issue}"])

        result_num = None
        if api:
            for _ in range(40):
                with session_lock:
                    if not sess.get('is_running'): break
                time.sleep(1.5)
                recents = api.get_recent_results(5, game_type_id, is_trx)
                for r in recents:
                    if str(r.get('issueNumber')) == issue:
                        result_num = int(r.get('number', 0))
                        break
                if result_num is not None: break
        else:
            time.sleep(5)
            result_num = random.randint(0, 9)

        if result_num is not None:
            actual_char = 'B' if result_num >= 5 else 'S'
            win = (pred_char == actual_char)
            with session_lock:
                if win:
                    profit = total_amount * 0.96
                    sess['current_step'] = 0
                    status_header = f"⚡ SIGMA MATRIX WIN +{profit:.2f} Ks"
                else:
                    profit = -total_amount
                    sess['current_step'] += 1
                    status_header = f"❌ PACKET MISSED -{total_amount:.2f} Ks"
                sess['total_profit'] += profit
                if virtual_mode:
                    sess['virtual_balance'] += profit
                    disp_bal = sess['virtual_balance']
                else:
                    server_bal = api.get_balance() if api else -1.0
                    if server_bal >= 0: sess['last_known_balance'] = server_bal
                    disp_bal = sess['last_known_balance']
            send_bet_quote(chat_id, [status_header, f"📊 FATE RESULT: {'BIG' if actual_char == 'B' else 'SMALL'} ({result_num})", f"🧩 NET VAULT BALANCE: {disp_bal:.2f} Ks", f"📈 CUMULATIVE PL: {sess['total_profit']:.2f} Ks"])
        else:
            send_message(chat_id, "<b>⚠️ Core stream sync timeout.</b>")

        time.sleep(1)

    with session_lock:
        if sess: sess['is_running'] = False

# ==================== MESSAGE HANDLER ====================
def process_message(chat_id, text, user_id):
    with session_lock:
        if user_id not in user_sessions:
            user_sessions[user_id] = get_default_session()
        sess = user_sessions[user_id]

    if text == "/start":
        send_message(chat_id, "<b>⚡ Welcome to Sigma Core Engine. Authenticate Grid.</b>", reply_markup=get_login_keyboard())
        return

    if text == "🔑 Secure Account Login":
        sess['input_state'] = 'login_phone'
        send_message(chat_id, "<b>📱 Enter Phone Number (Without 95):</b>")
        return
    if sess.get('input_state') == 'login_phone':
        sess['temp_phone'] = text.strip()
        sess['input_state'] = 'login_pwd'
        send_message(chat_id, "<b>🔑 Enter Password:</b>")
        return
    if sess.get('input_state') == 'login_pwd':
        api = LotteryAPI()
        ok, msg = api.login(sess['temp_phone'], text.strip())
        sess['input_state'] = None
        if ok:
            sess['api'] = api
            current_bal = api.get_balance()
            sess['last_known_balance'] = current_bal if current_bal >= 0 else 0.0
            send_message(chat_id, f"<b>⚡ 🔓 Access Granted!</b>\n<b>💳 WALLET: {sess['last_known_balance']:.2f} Ks</b>", reply_markup=get_main_keyboard())
        else:
            send_message(chat_id, f"<b>❌ Error: {clean_html(msg)}</b>", reply_markup=get_login_keyboard())
        return

    # Virtual Balance Setting (Matches Screenshot)
    if text == "💸 Set Virtual Balance":
        send_message(chat_id, "<b>Enter virtual balance amount:\nExample: 10000</b>")
        sess['input_state'] = 'set_virtual_balance'
        return
    if sess.get('input_state') == 'set_virtual_balance':
        try:
            val = float(text.strip())
            if val >= 0:
                sess['virtual_balance'] = val
                sess['virtual_mode'] = True
                send_message(chat_id, f"<b>🔄 Switched to Virtual Mode with {val:.0f} Ks</b>", reply_markup=get_main_keyboard())
            else:
                send_message(chat_id, "<b>❌ Amount must be positive.</b>", reply_markup=get_main_keyboard())
        except:
            send_message(chat_id, "<b>❌ Invalid number.</b>", reply_markup=get_main_keyboard())
        sess['input_state'] = None
        return

    if text == "📨 Test Styled Message":
        send_test_styled_message(chat_id)
        return

    if text == "⚙️ Bet Settings":
        send_message(chat_id, "<b>⚙️ Bet Options:</b>", reply_markup=get_bet_settings_keyboard())
        return
    if text == "🎯 Target Settings":
        send_message(chat_id, "<b>🎯 Target Options:</b>", reply_markup=get_target_settings_keyboard())
        return
    if text == "🔮 Strategy Menu":
        send_message(chat_id, "<b>🔮 Strategy Panel:</b>", reply_markup=get_strategy_menu_keyboard())
        return
    if text == "◀️ Main Menu":
        send_message(chat_id, "<b>Main Menu.</b>", reply_markup=get_main_keyboard())
        return

    # Strategy Activations
    if text == "⚡ Sigma Trend Core":
        sess['strategy_mode'] = 'SIGMA'
        send_message(chat_id, "<b>✅ Activated: Sigma Core.</b>", reply_markup=get_main_keyboard())
        return
    if text == "🔄 Smart Trend & Reversal":
        sess['strategy_mode'] = 'TREND_REVERSAL'
        send_message(chat_id, "<b>✅ Activated: Trend & Reversal.</b>", reply_markup=get_main_keyboard())
        return
    if text == "🎯 Pattern Hunter Engine":
        sess["strategy_mode"] = "PATTERN_HUNTER"
        send_message(chat_id, "<b>✅ Activated: Pattern Hunter.</b>", reply_markup=get_main_keyboard())
        return
    if text == "🧠 AI Trend Logic":
        sess["strategy_mode"] = "AI_TREND_LOGIC"
        send_message(chat_id, "<b>✅ Activated: AI Trend Logic.</b>", reply_markup=get_main_keyboard())
        return
    if text == "📈 Martingale":
        sess["strategy_mode"] = "MARTINGALE"
        send_message(chat_id, "<b>✅ Activated: Martingale.</b>", reply_markup=get_main_keyboard())
        return
    if text == "🔢 Fibonacci":
        sess["strategy_mode"] = "FIBONACCI"
        send_message(chat_id, "<b>✅ Activated: Fibonacci.</b>", reply_markup=get_main_keyboard())
        return
    if text == "🍀 Paroli":
        sess["strategy_mode"] = "PAROLI"
        send_message(chat_id, "<b>✅ Activated: Paroli.</b>", reply_markup=get_main_keyboard())
        return
    if text == "⚖️ D'Alembert":
        sess["strategy_mode"] = "DALEMBERT"
        send_message(chat_id, "<b>✅ Activated: D'Alembert.</b>", reply_markup=get_main_keyboard())
        return
    if text == "📊 Trend Following":
        sess["strategy_mode"] = "TREND_FOLLOWING"
        send_message(chat_id, "<b>✅ Activated: Trend Following.</b>", reply_markup=get_main_keyboard())
        return
    if text == "📊 Oscillator":
        sess["strategy_mode"] = "OSCILLATOR"
        send_message(chat_id, "<b>✅ Activated: Oscillator.</b>", reply_markup=get_main_keyboard())
        return
    if text == "🚀 Momentum":
        sess["strategy_mode"] = "MOMENTUM"
        send_message(chat_id, "<b>✅ Activated: Momentum.</b>", reply_markup=get_main_keyboard())
        return
    if text == "🔄 Mean Reversion":
        sess["strategy_mode"] = "MEAN_REVERSION"
        send_message(chat_id, "<b>✅ Activated: Mean Reversion.</b>", reply_markup=get_main_keyboard())
        return
    if text == "📜 Custom BS Order Pattern":
        sess['strategy_mode'] = 'BS_ORDER'
        sess['bs_custom_index'] = 0
        send_message(chat_id, "<b>✅ Activated: Custom Pattern.</b>", reply_markup=get_main_keyboard())
        return
    if text == "📝 Set Custom BS Order":
        send_message(chat_id, "<b>📝 Enter Pattern (e.g. BBSS):</b>")
        sess['input_state'] = 'set_custom_bs'
        return
    if sess.get('input_state') == 'set_custom_bs':
        clean_input = text.strip().upper()
        if all(char in ['B', 'S'] for char in clean_input):
            sess['bs_custom_sequence'] = list(clean_input)
            sess['bs_custom_index'] = 0
            send_message(chat_id, f"<b>✅ Pattern Saved: {clean_input}</b>", reply_markup=get_main_keyboard())
        else:
            send_message(chat_id, "<b>❌ Invalid. Use B/S only.</b>", reply_markup=get_main_keyboard())
        sess['input_state'] = None
        return

    if text == "💵 Set Base Amount":
        send_message(chat_id, "<b>Enter base amount:</b>")
        sess['input_state'] = 'set_base'
        return
    if sess.get('input_state') == 'set_base':
        try:
            val = int(text.strip())
            if val >= 10:
                sess['base_amount'] = val
                send_message(chat_id, f"<b>💎 Base set to: {val} Ks</b>", reply_markup=get_main_keyboard())
        except: pass
        sess['input_state'] = None
        return

    if text == "📊 Set Multiplier Sequence":
        send_message(chat_id, "<b>Enter sequence (e.g. 1 2 4):</b>")
        sess['input_state'] = 'set_seq'
        return
    if sess.get('input_state') == 'set_seq':
        try:
            seq = [int(x) for x in text.split() if x.strip().isdigit()]
            if seq:
                sess['betting_sequence'] = seq
                sess['current_step'] = 0
                send_message(chat_id, f"<b>💎 Sequence updated.</b>", reply_markup=get_main_keyboard())
        except: pass
        sess['input_state'] = None
        return

    if text == "🎮 Select Game Type":
        send_message(chat_id, "<b>Select Room:</b>", reply_markup=get_game_type_keyboard())
        return
    for key, gt in GAME_TYPES.items():
        if text == gt['name']:
            sess['game_key'] = key
            send_message(chat_id, f"<b>💎 Room: {gt['name']}</b>", reply_markup=get_main_keyboard())
            return

    if text == "🧧 Set Profit Target":
        send_message(chat_id, "<b>Enter profit target:</b>")
        sess['input_state'] = 'set_target'
        return
    if sess.get('input_state') == 'set_target':
        try:
            sess['profit_target'] = float(text.strip())
            send_message(chat_id, f"<b>💎 Target set.</b>", reply_markup=get_main_keyboard())
        except: pass
        sess['input_state'] = None
        return

    if text == "🛑 Set Stop Loss":
        send_message(chat_id, "<b>Enter stop loss:</b>")
        sess['input_state'] = 'set_stop'
        return
    if sess.get('input_state') == 'set_stop':
        try:
            sess['stop_loss'] = float(text.strip())
            send_message(chat_id, f"<b>💎 Stop loss set.</b>", reply_markup=get_main_keyboard())
        except: pass
        sess['input_state'] = None
        return

    if text == "🔄 Virtual Switch":
        sess['virtual_mode'] = not sess['virtual_mode']
        send_message(chat_id, f"<b>⚡ Mode: {'VIRTUAL' if sess['virtual_mode'] else 'REAL'}</b>")
        return
    if text == "📊 Check Info Dashboard":
        send_beautiful_dashboard(chat_id, sess)
        return
    if text == "▶️ Start Engine":
        if sess['is_running']:
            send_message(chat_id, "<b>⚠️ Already running!</b>")
        else:
            sess['is_running'] = True
            sess['total_profit'] = 0.0
            sess['current_step'] = 0
            threading.Thread(target=betting_loop, args=(user_id, chat_id), daemon=True).start()
        return
    if text == "⏹️ Stop Engine":
        sess['is_running'] = False
        send_message(chat_id, "<b>🛑 Stopping...</b>")
        return
    if text == "🚪 Secure Logout":
        sess['is_running'] = False
        with session_lock:
            user_sessions[user_id] = get_default_session()
        send_message(chat_id, "<b>🚪 Logged out.</b>", reply_markup=get_login_keyboard())
        return

# ==================== MAIN RUNNER ====================
def get_updates(offset=None):
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"timeout": 10}
    if offset: params["offset"] = offset
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200: return resp.json().get("result", [])
    except: pass
    return []

def main():
    print("🚀 Sigma Stable Engine Active...")
    last_update_id = 0
    while True:
        updates = get_updates(offset=last_update_id + 1)
        for update in updates:
            last_update_id = update['update_id']
            if 'message' in update:
                msg = update['message']
                process_message(msg['chat']['id'], msg.get('text', ''), msg['from']['id'])
        time.sleep(0.5)

if __name__ == "__main__":
    main()
