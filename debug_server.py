import requests
import os

# --- 設定（ローカルテスト用） ---
# サーバーが起動しているURL
BASE_URL = "http://127.0.0.1:5000"
# スプレッドシートに登録したテスト用メールアドレス
TEST_EMAIL = "test@example.com" 
# テスト用画像パス（同じフォルダに画像がない場合はスキップされます）
TEST_IMAGE = "debug_input.png" 

def run_debug():
    print("=== Universal Lister Pro サーバー診断開始 ===")
    print(f"接続先: {BASE_URL}")
    
    token = None

    # 1. 認証エンドポイントのテスト
    print("\n[1/3] 認証チェック (/auth)...")
    try:
        res = requests.post(f"{BASE_URL}/auth", json={"email": TEST_EMAIL})
        print(f"ステータス: {res.status_code}")
        data = res.json()
        if res.status_code == 200:
            token = data.get("token")
            print(f"成功！トークン取得: {token[:8]}...")
            print(f"有効期限: {data.get('expires')}")
        else:
            print(f"失敗: {data.get('error')}")
    except Exception as e:
        print(f"サーバーに接続できません: {e}")
        return

    # 2. 翻訳エンドポイントのテスト
    if token:
        print("\n[2/3] 翻訳チェック (/translate)...")
        try:
            test_text = "Hello, this is a debug test."
            res = requests.post(f"{BASE_URL}/translate", json={
                "token": token,
                "text": test_text
            })
            print(f"ステータス: {res.status_code}")
            if res.status_code == 200:
                print(f"レスポンス: {res.json().get('translatedText')}")
            else:
                print(f"失敗: {res.json().get('error')}")
        except Exception as e:
            print(f"エラー発生: {e}")

    # 3. 画像処理エンドポイントのテスト
    if token:
        print("\n[3/3] AI背景削除チェック (/process_image)...")
        if not os.path.exists(TEST_IMAGE):
            print(f"スキップ: テスト用画像 '{TEST_IMAGE}' が見つかりません。")
        else:
            try:
                with open(TEST_IMAGE, "rb") as f:
                    res = requests.post(
                        f"{BASE_URL}/process_image",
                        data={"token": token},
                        files={"image": f}
                    )
                print(f"ステータス: {res.status_code}")
                if res.status_code == 200:
                    with open("debug_output.png", "wb") as out:
                        out.write(res.content)
                    print("成功！加工済み画像を 'debug_output.png' として保存しました。")
                else:
                    print(f"失敗: {res.json().get('error')}")
            except Exception as e:
                print(f"エラー発生: {e}")

    print("\n=== 診断終了 ===")

if __name__ == "__main__":
    # 簡易的にテスト画像を作成（画像がない場合用）
    if not os.path.exists(TEST_IMAGE):
        try:
            from PIL import Image
            img = Image.new('RGB', (100, 100), color = 'red')
            img.save(TEST_IMAGE)
            print(f"テスト用ダミー画像 '{TEST_IMAGE}' を生成しました。")
        except:
            pass
            
    run_debug()