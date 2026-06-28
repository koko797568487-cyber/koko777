import requests
import json
import time
import hashlib
import random
import math
from config import API_BASE, HEADERS

# ==================== API CLASS ====================
class LotteryAPI:
    def __init__(self):
        self.headers = HEADERS.copy()
        self.token = ""
        self.user_id = "Unknown"

    def sign_md5(self, data_dict):
        sign_data = data_dict.copy()
        for k in ['signature','timestamp']:
            if k in sign_data: del sign_data[k]
        sorted_data = dict(sorted(sign_data.items()))
        hash_string = json.dumps(sorted_data, separators=(',', ':'))
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()

    def random_key(self):
        xxxx = "xxxxxxxxxxxx4xxxyxxxxxxxxxxxxxxx"
        return ''.join(random.choice('0123456789abcdef') if c=='x' else random.choice('89a') if c=='y' else c for c in xxxx)

    def login(self, phone, password):
        try:
            clean_phone = phone.replace("95", "") if phone.startswith("95") else phone
            username = f"95{clean_phone}"
            body = {
                "phonetype": -1, "language": 0, "logintype": "mobile",
                "random": "9078efc98754430e92e51da59eb2563c",
                "username": username, "pwd": password, "timestamp": int(time.time())
            }
            body["signature"] = self.sign_md5(body).upper()
            resp = requests.post(f"{API_BASE}Login", headers=self.headers, json=body, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('msgCode') == 0:
                    tok = data.get('data', {})
                    self.token = f"{tok.get('tokenHeader','')}{tok.get('token','')}"
                    self.headers["Authorization"] = self.token
                    self.user_id = str(tok.get('id', 'Unknown'))
                    return True, "Success"
                return False, data.get('msg', 'Login Error')
            return False, f"Server Error: {resp.status_code}"
        except Exception as e:
            return False, f"Error: {e}"

    def get_balance(self):
        for _ in range(3):
            try:
                body = {"language":0,"random":"9078efc98754430e92e51da59eb2563c","timestamp":int(time.time())}
                body["signature"] = self.sign_md5(body).upper()
                resp = requests.post(f"{API_BASE}GetBalance", headers=self.headers, json=body, timeout=6)
                if resp.status_code == 200:
                    d = resp.json()
                    if d.get('msgCode') == 0:
                        return float(d.get('data',{}).get('amount', 0))
            except:
                time.sleep(1)
        return -1.0

    def get_current_issue(self, type_id):
        try:
            body = {"typeId": type_id, "language":0, "random":"b05034ba4a2642009350ee863f29e2e9", "timestamp": int(time.time())}
            body["signature"] = self.sign_md5(body).upper()
            resp = requests.post(f"{API_BASE}GetGameIssue", headers=self.headers, json=body, timeout=5)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('msgCode') == 0:
                    return d.get('data',{}).get('issueNumber','')
            return ""
        except:
            return ""

    def place_bet(self, issue, base_amount, bet_count, bet_type, type_id):
        try:
            body = {
                "typeId": type_id, "issuenumber": issue, "language": 0, "gameType": 2,
                "amount": base_amount, "betCount": bet_count, "selectType": bet_type,
                "random": self.random_key(), "timestamp": int(time.time())
            }
            body["signature"] = self.sign_md5(body).upper()
            resp = requests.post(f"{API_BASE}GameBetting", headers=self.headers, json=body, timeout=5)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('code') == 0 or d.get('msgCode') == 0:
                    return True, "Success", int((base_amount * bet_count) * 0.96)
                return False, d.get('msg','Bet Failed'), 0
            return False, f"API error {resp.status_code}", 0
        except Exception as e:
            return False, f"Bet error: {e}", 0

    def get_recent_results(self, count, type_id, is_trx=False):
        try:
            endpoint = f"{API_BASE}GetTRXNoaverageEmerdList" if is_trx else f"{API_BASE}GetNoaverageEmerdList"
            body = {
                "pageNo": 1, "pageSize": count, "language": 0, "typeId": type_id,
                "random": "6DEB0766860C42151A193692ED16D65A", "timestamp": int(time.time())
            }
            body["signature"] = self.sign_md5(body).upper()
            resp = requests.post(endpoint, headers=self.headers, json=body, timeout=5)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('msgCode') == 0:
                    data_obj = d.get('data', {})
                    if is_trx:
                        return data_obj.get('data', {}).get('gameslist', [])
                    else:
                        return data_obj.get('list', [])
            return []
        except:
            return []

# ==================== STRATEGY ENGINES ====================
class SmartTrendReversalEngine:
    def predict(self, numbers_all):
        if not numbers_all or len(numbers_all) < 8:
            return 5, "BIG", "insufficient data"
        weights = [1.0, 1.2, 1.5, 1.8, 2.1, 2.5, 3.0, 3.5]
        recent = numbers_all[:min(8, len(numbers_all))]
        w_sum = sum(recent[i] * weights[i] for i in range(len(recent)))
        w_avg = w_sum / sum(weights[:len(recent)])
        last_three = recent[:3]
        all_big = all(x >= 5 for x in last_three)
        all_small = all(x < 5 for x in last_three)
        reversal_signal = None
        if all_big: reversal_signal = "SMALL"
        elif all_small: reversal_signal = "BIG"
        if reversal_signal:
            final_side = reversal_signal
            confidence = 85
        else:
            final_side = "BIG" if w_avg >= 5 else "SMALL"
            confidence = min(95, int(55 + abs(w_avg - 5) * 4))
        sigma_idx = round(w_avg)
        sigma_idx = max(0, min(9, sigma_idx))
        return sigma_idx, final_side, f"Trend/Rev (conf {confidence}%)"

class PatternHunterEngine:
    def predict(self, numbers_all):
        if not numbers_all or len(numbers_all) < 10:
            return 5, "BIG", "Pattern Hunter (Insuff. Data)"
        seq = ['B' if n >= 5 else 'S' for n in numbers_all]
        current_pattern = seq[:3]
        history = seq[3:]
        next_b = 0
        next_s = 0
        for i in range(len(history) - 3):
            if history[i:i+3] == current_pattern:
                if i > 0:
                    followed_by = history[i-1]
                    if followed_by == 'B': next_b += 1
                    else: next_s += 1
        if next_b > next_s:
            side = "BIG"
            conf = 70 + min(25, next_b * 5)
        elif next_s > next_b:
            side = "SMALL"
            conf = 70 + min(25, next_s * 5)
        else:
            b_count = seq.count('B')
            side = "BIG" if b_count >= len(seq)/2 else "SMALL"
            conf = 60
        sigma_idx = 9 if side == "BIG" else 0
        return sigma_idx, side, f"Pattern Hunter (conf {conf}%)"

class AILogicTrendStrategyEngine:
    def predict(self, numbers_all):
        if not numbers_all or len(numbers_all) < 10:
            return 5, "BIG", "AI Trend Logic (Insuff. Data)"
        seq = ['B' if n >= 5 else 'S' for n in numbers_all]
        recent_five = seq[:5]
        big_count_recent = recent_five.count('B')
        small_count_recent = recent_five.count('S')
        overall_ten = seq[:10]
        big_count_overall = overall_ten.count('B')
        small_count_overall = overall_ten.count('S')
        predicted_side = "BIG"
        confidence = 65
        if len(seq) >= 3:
            last_three = seq[:3]
            if all(s == 'B' for s in last_three):
                predicted_side = 'B'
                confidence = 80
            elif all(s == 'S' for s in last_three):
                predicted_side = 'S'
                confidence = 80
        if confidence == 65:
            if big_count_recent > small_count_recent:
                predicted_side = 'B'
                confidence = 70 + (big_count_recent - small_count_recent) * 5
            elif small_count_recent > big_count_recent:
                predicted_side = 'S'
                confidence = 70 + (small_count_recent - big_count_recent) * 5
        if confidence == 65:
            if big_count_overall > small_count_overall:
                predicted_side = 'B'
                confidence = 68 + (big_count_overall - small_count_overall) * 2
            elif small_count_overall > big_count_overall:
                predicted_side = 'S'
                confidence = 68 + (small_count_overall - big_count_overall) * 2
        if confidence == 65:
            predicted_side = seq[0] if seq else 'B'
        sigma_idx = 9 if predicted_side == "BIG" else 0
        confidence = min(95, max(60, confidence))
        return sigma_idx, predicted_side, f"AI Trend Logic (conf {confidence}%)"

class MartingaleStrategyEngine:
    def predict(self, numbers_all, current_step):
        if not numbers_all or len(numbers_all) < 1:
            return 5, "BIG", "Martingale (Insuff. Data)"
        last_result = numbers_all[0]
        predicted_side = "BIG" if last_result >= 5 else "SMALL"
        return 5, predicted_side, f"Martingale (Step {current_step})"

class FibonacciStrategyEngine:
    def predict(self, numbers_all, current_step):
        if not numbers_all or len(numbers_all) < 1:
            return 5, "BIG", "Fibonacci (Insuff. Data)"
        last_result = numbers_all[0]
        predicted_side = "BIG" if last_result >= 5 else "SMALL"
        return 5, predicted_side, f"Fibonacci (Step {current_step})"

class ParoliStrategyEngine:
    def predict(self, numbers_all, last_win):
        if not numbers_all or len(numbers_all) < 3:
            return 5, "BIG", "Paroli (Insuff. Data)"
        big_count = sum(1 for n in numbers_all[:3] if n >= 5)
        small_count = sum(1 for n in numbers_all[:3] if n < 5)
        predicted_side = "BIG" if big_count >= small_count else "SMALL"
        confidence = 65 + abs(big_count - small_count) * 10
        return 5, predicted_side, f"Paroli (Conf {confidence}%)"

class DAlembertStrategyEngine:
    def predict(self, numbers_all):
        if not numbers_all or len(numbers_all) < 5:
            return 5, "BIG", "D'Alembert (Insuff. Data)"
        big_count = sum(1 for n in numbers_all[:5] if n >= 5)
        small_count = sum(1 for n in numbers_all[:5] if n < 5)
        predicted_side = "BIG" if big_count >= small_count else "SMALL"
        confidence = 60 + abs(big_count - small_count) * 5
        return 5, predicted_side, f"D'Alembert (Conf {confidence}%)"

class TrendFollowingStrategyEngine:
    def predict(self, numbers_all):
        if not numbers_all or len(numbers_all) < 5:
            return 5, "BIG", "Trend Following (Insuff. Data)"
        recent_results = numbers_all[:5]
        big_count = sum(1 for n in recent_results if n >= 5)
        small_count = sum(1 for n in recent_results if n < 5)
        if big_count > small_count:
            predicted_side = "BIG"
            confidence = 75 + (big_count - small_count) * 5
        elif small_count > big_count:
            predicted_side = "SMALL"
            confidence = 75 + (small_count - big_count) * 5
        else:
            predicted_side = "BIG" if numbers_all[0] >= 5 else "SMALL"
            confidence = 65
        sigma_idx = 9 if predicted_side == "BIG" else 0
        confidence = min(95, max(60, confidence))
        return sigma_idx, predicted_side, f"Trend Following (conf {confidence}%)"

class OscillatorStrategyEngine:
    def predict(self, numbers_all):
        if not numbers_all or len(numbers_all) < 10:
            return 5, "BIG", "Oscillator (Insuff. Data)"
        recent = numbers_all[:10]
        avg_recent = sum(recent) / len(recent)
        avg_all = sum(numbers_all[:20]) / min(20, len(numbers_all)) if len(numbers_all) >= 20 else avg_recent
        diff = avg_recent - avg_all
        if diff > 0.5:
            side = "BIG"
            conf = 70 + min(20, int(diff*10))
        elif diff < -0.5:
            side = "SMALL"
            conf = 70 + min(20, int(abs(diff)*10))
        else:
            side = "BIG" if avg_recent >= 5 else "SMALL"
            conf = 60
        sigma_idx = 9 if side == "BIG" else 0
        return sigma_idx, side, f"Oscillator (conf {conf}%)"

class MomentumStrategyEngine:
    def predict(self, numbers_all):
        if not numbers_all or len(numbers_all) < 12:
            return 5, "BIG", "Momentum (Insuff. Data)"
        recent = numbers_all[:5]
        older = numbers_all[5:10]
        avg_recent = sum(recent)/len(recent)
        avg_older = sum(older)/len(older)
        diff = avg_recent - avg_older
        if diff > 0.3:
            side = "BIG"
            conf = 70 + min(20, int(diff*15))
        elif diff < -0.3:
            side = "SMALL"
            conf = 70 + min(20, int(abs(diff)*15))
        else:
            side = "BIG" if avg_recent >= 5 else "SMALL"
            conf = 60
        sigma_idx = 9 if side == "BIG" else 0
        return sigma_idx, side, f"Momentum (conf {conf}%)"

class MeanReversionStrategyEngine:
    def predict(self, numbers_all):
        if not numbers_all or len(numbers_all) < 8:
            return 5, "BIG", "Mean Reversion (Insuff. Data)"
        last = numbers_all[0]
        if last >= 8:
            side = "SMALL"
            conf = 80
        elif last <= 1:
            side = "BIG"
            conf = 80
        else:
            avg = sum(numbers_all[:5])/5
            side = "BIG" if avg >= 5 else "SMALL"
            conf = 65
        sigma_idx = 9 if side == "BIG" else 0
        return sigma_idx, side, f"Mean Reversion (conf {conf}%)"

class SigmaStrategyEngine:
    def compute_sigma_prediction(self, numbers_all):
        if not numbers_all or len(numbers_all) < 5:
            return 5, "BIG"
        recent = numbers_all[:7]
        weights = [3.0, 2.0, 1.5, 1.0, 0.8, 0.5, 0.4]
        weighted_sum = 0
        total_weight = 0
        for i in range(len(recent)):
            if i < len(weights):
                weighted_sum += recent[i] * weights[i]
                total_weight += weights[i]
        sigma_index = round(weighted_sum / total_weight)
        sigma_index = max(0, min(9, sigma_index))
        size_pred = "BIG" if sigma_index >= 5 else "SMALL"
        return sigma_index, size_pred

    def get_sigma_stability(self, numbers_all):
        if not numbers_all or len(numbers_all) < 8:
            return 72
        sub_list = numbers_all[:10]
        mean = sum(sub_list) / len(sub_list)
        variance = sum((n - mean) ** 2 for n in sub_list) / len(sub_list)
        std = math.sqrt(variance)
        stability = 92 - min(40, int(std * 3.5))
        return min(98, max(60, stability))
