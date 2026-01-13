import os
import io
import uuid
import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from rembg import remove
from PIL import Image
from googleapiclient.discovery import build
from google.oauth2 import service_account

app = Flask(__name__)

# --- 設定項目 ---
# 環境変数からの読み込み。未設定時はプレースホルダをデフォルトに設定
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', 'ここにスプレッドシートのIDを記入')
SHEET_NAME = 'Sheet1'
TOKEN_EXPIRY_HOURS = 6 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# 【微調整1】起動時に設定不備があればエラーを出し、運営者のミスを未然に防ぐ
#if not SPREADSHEET_ID or "ここにスプレッドシート" in SPREADSHEET_ID:
#    raise RuntimeError("【起動エラー】SPREADSHEET_IDが環境変数に設定されていないか、デフォルトのままです。")

# --- セキュリティ設定：CORSを環境変数で制御 ---
# 【微調整3】環境変数が空の場合は全拒否（空リスト）にする
allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

CORS(app, resources={
    r"/*": {
        "origins": ALLOWED_ORIGINS
    }
})

# トークン管理用（メモリ保持）
active_tokens = {}

# 【微調整2】トークンチェック処理の共通化
def is_token_valid(token: str) -> bool:
    """トークンが有効かつ期限内であるかを確認する"""
    if not token:
        return False
    t_data = active_tokens.get(token)
    return bool(t_data) and t_data["expiry"] > datetime.datetime.now()

def get_sheets_service():
    if os.path.exists('service_account.json'):
        creds = service_account.Credentials.from_service_account_file(
            'service_account.json', scopes=SCOPES)
        return build('sheets', 'v4', credentials=creds)
    return None

@app.route('/health', methods=['GET'])
def health():
    """サーバーの稼働確認用エンドポイント"""
    return jsonify({
        "status": "ok", 
        "timestamp": str(datetime.datetime.now()),
        "service_account": os.path.exists('service_account.json')
    })

@app.route('/auth', methods=['POST'])
def auth():
    global active_tokens
    # スプレッドシートを無視して、ダミーのトークンを即座に発行
    token = "debug-test-token-12345"
    active_tokens[token] = {
        "email": "test@example.com",
        "expiry": datetime.datetime.now() + datetime.timedelta(hours=24)
    }
    return jsonify({
        "token": token,
        "expires": "2099-12-31"
    })

@app.route('/process_image', methods=['POST'])
def process_image():
    token = request.form.get('token')
    
    # 共通関数によるトークンチェック
    if not is_token_valid(token):
        return jsonify({"error": "unauthorized"}), 403

    if 'image' not in request.files:
        return jsonify({"error": "no_image"}), 400
    
    fs = request.files['image']

    try:
        # FileStorageのstreamからサイズを取得
        fs.stream.seek(0, os.SEEK_END)
        file_size = fs.stream.tell()
        fs.stream.seek(0)
        
        if file_size > 5 * 1024 * 1024:
            return jsonify({"error": "file_too_large"}), 413

        input_image = Image.open(fs.stream)
        # 背景削除実行 (rembg)
        output_image = remove(input_image)
        
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": f"processing_failed: {str(e)}"}), 500

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    if not data:
        return jsonify({"error": "invalid_request"}), 400
        
    token = data.get('token')
    text = data.get('text')
    
    # 共通関数によるトークンチェック
    if not is_token_valid(token):
        return jsonify({"error": "unauthorized"}), 403

    # 現在はパススルー（翻訳ロジック未実装）
    translated_text = text 
    
    return jsonify({"translatedText": translated_text})

if __name__ == '__main__':
    is_debug = os.environ.get('FLASK_DEBUG') == '1'
    app.run(debug=is_debug, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
