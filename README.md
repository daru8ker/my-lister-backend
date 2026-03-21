Universal Lister Pro
バックエンドサーバー管理マニュアル（運営者向け）

本プログラムは、Universal Lister Pro 拡張機能から利用される
以下の機能を提供するバックエンドサーバーです。

生徒（ユーザー）の利用可否管理

AIによる画像背景削除

翻訳機能（※現在はパススルー実装）

1. 動作環境

Python 3.10 以上

対応OS：Linux / macOS / Windows

推奨ホスティング：Render（Web Service）
※ Railway / Fly.io / VPS 等でも動作します

2. 導入手順（初回のみ）
2-1. Google Sheets API の設定

Google Cloud Console にログイン

対象プロジェクトで Google Sheets API を有効化

サービスアカウントを作成

JSONキーを発行

ファイル名を service_account.json に変更し、
本フォルダ（backend/）直下に配置してください

⚠️ service_account.json は 配布物に含めないでください
クライアント（運営者）が自身で発行・管理する必要があります。

2-2. 管理用スプレッドシートの準備

以下の構成で Google スプレッドシートを作成してください。

列	内容
A列	email（生徒のメールアドレス）
B列	status（active / blocked）
C列	expires（有効期限：YYYY-MM-DD 形式）

作成後、共有設定から
サービスアカウントのメールアドレスを 閲覧者 として追加してください。

2-3. 環境変数の設定

サーバー側で以下の環境変数を設定してください。

必須

SPREADSHEET_ID

管理用スプレッドシートのID
（URL内の長い英数字）

推奨

ALLOWED_ORIGINS

拡張機能IDおよび本番ドメインをカンマ区切りで指定

例：

chrome-extension://xxxxx,https://xxx.onrender.com

ローカルテスト時

.env ファイルを作成し、上記を記載してください。

3. 主要エンドポイント一覧
メソッド	パス	内容
GET	/health	サーバーの稼働確認
POST	/auth	生徒認証・トークン発行
POST	/process_image	AI背景削除
POST	/translate	翻訳処理（現在はパススルー）
4. 運用・保守について
4-1. 生徒の利用管理

新規利用許可

スプレッドシートにメールを追加し、status=active

利用停止・未払い対応

status=blocked に変更

期限切れ

expires を過ぎると自動的に利用不可になります

※ トークンは メモリ管理のため、
サーバー再起動時は生徒が再ログインする必要があります。

4-2. サーバー診断

同封の debug_server.py を実行することで、

認証

API応答

背景削除処理
が正常に動作しているか確認できます。

5. 注意事項・仕様上の制限

翻訳機能は 現状パススルー実装です
（商用で利用する場合は DeepL / Google 翻訳 API 等の接続が必要）

トークン管理は簡易実装のため、

大規模運用時は Redis / JWT 等への移行を推奨します

画像処理は 最大5MB まで対応しています

6. ライセンス・使用ライブラリ

本プログラムは以下のOSSを使用しています。

Flask（Webフレームワーク）

rembg（AI背景削除）

Pillow (PIL)（画像処理）

Google Sheets API
