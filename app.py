import os
import io
import uuid
import datetime
import requests as http_requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from rembg import remove
from PIL import Image
from deep_translator import GoogleTranslator

app = Flask(__name__)

# ============================================================
# CORS設定
# ============================================================
allowed_origins_env = os.environ.get('ALLOWED_ORIGINS', '*')
if allowed_origins_env == '*':
    CORS(app)
else:
    origins = [o.strip() for o in allowed_origins_env.split(',')]
    CORS(app, origins=origins)

# ============================================================
# GAS認証URL（Google Apps Script）
# ============================================================
GAS_AUTH_URL = os.environ.get(
    'GAS_AUTH_URL',
    'https://script.google.com/macros/s/AKfycbxql4_Wm1SsAj2u5CslyeOUbxPpT22-iHp_PgTaE4yHb5g4KHYA-hw2MgxGgFuRvDTIyw/exec'
)

# ============================================================
# トークン管理（メモリ）
# ============================================================
active_tokens = {}

def is_token_valid(token: str) -> bool:
    if not token:
        return False
    t_data = active_tokens.get(token)
    return bool(t_data) and t_data['expiry'] > datetime.datetime.now()

# ============================================================
# ヘルスチェック
# ============================================================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "mode": "production",
        "auth": "GAS"
    })

# ============================================================
# 認証（GAS経由でスプレッドシートを確認）
# ============================================================
@app.route('/auth', methods=['POST'])
def auth():
    data = request.json or {}
    email = data.get('email', '').strip()

    if not email:
        return jsonify({"error": "email_required"}), 400

    # GASに問い合わせ
    try:
        gas_res = http_requests.post(
            GAS_AUTH_URL,
            json={"email": email},
            timeout=10
        )
        gas_data = gas_res.json()
    except Exception as e:
        return jsonify({"error": "auth_service_unavailable", "detail": str(e)}), 503

    # GASからのレスポンスを判定
    # 期待するGASレスポンス例: {"status": "ok", "expires": "2025-12-31"}
    #                  or     {"status": "error", "reason": "not_found"}
    gas_status = gas_data.get('status', '')

    if gas_status != 'ok':
        reason = gas_data.get('reason', 'unauthorized')
        return jsonify({"error": reason}), 403

    # 有効期限（GASが返す場合）
    expires_str = gas_data.get('expires', '')

    # トークン発行
    token = str(uuid.uuid4())
    expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
    active_tokens[token] = {'email': email, 'expiry': expiry}

    return jsonify({
        "token": token,
        "expires": expiry.strftime('%Y-%m-%d %H:%M')
    })

# ============================================================
# 画像背景削除
# ============================================================
@app.route('/process_image', methods=['POST'])
def process_image():
    token = request.form.get('token')
    if not is_token_valid(token):
        return jsonify({"error": "unauthorized"}), 403

    if 'image' not in request.files:
        return jsonify({"error": "no_image"}), 400

    fs = request.files['image']

    # ファイルサイズ制限（5MB）
    fs.seek(0, 2)
    size = fs.tell()
    fs.seek(0)
    if size > 5 * 1024 * 1024:
        return jsonify({"error": "image_too_large"}), 413

    try:
        input_image = Image.open(fs.stream)
        output_image = remove(input_image)
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# 翻訳
# ============================================================
@app.route('/translate', methods=['POST'])
def translate():
    data = request.json or {}
    token = data.get('token')
    if not is_token_valid(token):
        return jsonify({"error": "unauthorized"}), 403

    text = data.get('text', '')
    try:
        if text and len(text.strip()) > 0:
            translated_text = GoogleTranslator(source='ja', target='en').translate(text)
        else:
            translated_text = text
    except Exception:
        translated_text = text

    return jsonify({"translatedText": translated_text})

# ============================================================
# エントリーポイント
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)