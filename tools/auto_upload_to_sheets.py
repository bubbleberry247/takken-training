#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheets自動アップロードスクリプト（gspread + OAuth2認証）

使用方法:
  python auto_upload_to_sheets.py

認証情報:
  - clasp認証情報（.clasprc.json）を自動的に使用
  - サービスアカウントまたはOAuth2認証に対応
"""
import sys
import io
import csv
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 設定
CSV_FILE = Path(__file__).parent / 'questionbank_drive_import.csv'
SPREADSHEET_ID = '1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0'
SHEET_NAME = 'QuestionBank'
PROJECT_DIR = Path(__file__).parent.parent
CLASP_RC_FILE = PROJECT_DIR / '.clasprc.json'
CREDENTIALS_DIR = Path.home() / '.config' / 'gspread'
SERVICE_ACCOUNT_FILE = CREDENTIALS_DIR / 'credentials.json'

# Google Sheets APIのスコープ
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_credentials():
    """認証情報を取得（clasp認証、サービスアカウント、またはOAuth2）"""

    # サービスアカウント認証を試す
    if SERVICE_ACCOUNT_FILE.exists():
        print(f"  - サービスアカウント認証を使用: {SERVICE_ACCOUNT_FILE}")
        creds = Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE),
            scopes=SCOPES
        )
        return creds

    # clasp認証情報を試す
    if CLASP_RC_FILE.exists():
        print(f"  - clasp認証情報を使用: {CLASP_RC_FILE}")
        with open(CLASP_RC_FILE, 'r', encoding='utf-8') as f:
            clasp_data = json.load(f)

        # clasp tokenからOAuth2認証情報を作成
        token_data = clasp_data.get('token', {})

        # claspのスコープに含まれているものを使用（Sheetsアクセスには drive.file スコープで十分）
        clasp_scopes = token_data.get('scope', '').split(' ')

        # OAuthCredentials形式に変換
        creds = OAuthCredentials(
            token=token_data.get('access_token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=clasp_data.get('oauth2ClientSettings', {}).get('clientId'),
            client_secret=clasp_data.get('oauth2ClientSettings', {}).get('clientSecret'),
            scopes=clasp_scopes  # clasp認証のスコープをそのまま使用
        )

        # トークンの有効性を確認し、期限切れなら更新
        if creds.expired and creds.refresh_token:
            print("  - トークンを更新中...")
            creds.refresh(Request())

        return creds

    # 認証情報が見つからない場合
    print("\n" + "=" * 70)
    print("❌ 認証情報が見つかりません")
    print("=" * 70)
    print("\n以下のいずれかのファイルを配置してください:")
    print(f"\n1. clasp認証情報（推奨）:")
    print(f"   {CLASP_RC_FILE}")
    print(f"\n2. サービスアカウント認証:")
    print(f"   {SERVICE_ACCOUNT_FILE}")
    print("=" * 70)
    sys.exit(1)


def main():
    print("=" * 70)
    print("Google Sheets 自動アップロード（gspread + OAuth2）")
    print("=" * 70)

    # ステップ1: CSVファイルの存在確認と読み込み
    print(f"\n[1/4] CSVファイルを確認中...")
    if not CSV_FILE.exists():
        print(f"❌ CSVファイルが見つかりません: {CSV_FILE}")
        sys.exit(1)

    print(f"  ✅ ファイル確認: {CSV_FILE.name}")
    print(f"  - フルパス: {CSV_FILE.absolute()}")

    # CSVデータを読み込み
    print(f"\n[2/4] CSVデータを読み込み中...")
    rows = []
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)

    if len(rows) == 0:
        print("❌ CSVファイルが空です")
        sys.exit(1)

    headers = rows[0]
    data_rows = rows[1:]

    print(f"  ✅ 読み込み完了:")
    print(f"     - ヘッダー: {len(headers)}列")
    print(f"     - データ: {len(data_rows)}問")

    # ステップ2: Google Sheets APIに接続
    print(f"\n[3/4] Google Sheets APIに接続中...")
    try:
        creds = get_credentials()
        client = gspread.authorize(creds)
        print("  ✅ 認証成功")
    except Exception as e:
        print(f"❌ 認証エラー: {e}")
        sys.exit(1)

    # スプレッドシートを開く
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        print(f"  ✅ スプレッドシートを開きました: {spreadsheet.title}")
    except gspread.exceptions.APIError as e:
        print(f"❌ スプレッドシートを開けません:")
        print(f"   APIエラー: {e}")

        # 詳細なエラー情報を取得
        error_details = str(e.response.text) if hasattr(e, 'response') else str(e)

        # Google Sheets APIが有効化されていない場合の対処法を表示
        if 'Google Sheets API has not been used' in error_details or '[403]' in str(e):
            print("\n" + "=" * 70)
            print("Google Sheets APIの有効化が必要です")
            print("=" * 70)
            print("\n以下の手順でAPIを有効化してください:")
            print("\n1. 以下のURLをブラウザで開く:")

            # エラーメッセージからプロジェクトIDを抽出
            import re
            match = re.search(r'project (\d+)', error_details)
            if match:
                project_id = match.group(1)
                print(f"   https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project={project_id}")
            else:
                print("   https://console.cloud.google.com/apis/library/sheets.googleapis.com")

            print("\n2. 「有効にする」ボタンをクリック")
            print("\n3. 数分待ってから、このスクリプトを再実行")
            print("=" * 70)

        sys.exit(1)
    except PermissionError as e:
        print(f"❌ 権限エラー:")
        print(f"   {e}")
        print("\n" + "=" * 70)
        print("Google Sheets APIの有効化が必要です")
        print("=" * 70)
        print("\n以下の手順でAPIを有効化してください:")
        print("\n1. 以下のURLをブラウザで開く:")
        print("   https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=1072944905499")
        print("\n2. 「有効にする」ボタンをクリック")
        print("\n3. 数分待ってから、このスクリプトを再実行")
        print("=" * 70)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 予期しないエラー:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # シートを取得または作成
    try:
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        print(f"  ✅ シートを取得: {SHEET_NAME}")
    except gspread.exceptions.WorksheetNotFound:
        print(f"  ⚠️  シート '{SHEET_NAME}' が見つかりません。新規作成します...")
        worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=len(rows), cols=len(headers))
        print(f"  ✅ シートを作成: {SHEET_NAME}")

    # ステップ3: データをアップロード
    print(f"\n[4/4] データをアップロード中...")
    print(f"  - スプレッドシートID: {SPREADSHEET_ID}")
    print(f"  - シート名: {SHEET_NAME}")
    print(f"  - アップロード件数: {len(rows)}行（ヘッダー含む）")

    try:
        # 既存のデータを全削除
        print(f"  - 既存データをクリア中...")
        worksheet.clear()

        # 新しいデータを一括アップロード
        print(f"  - 新しいデータをアップロード中...")
        worksheet.update(range_name='A1', values=rows)

        print(f"\n" + "=" * 70)
        print(f"✅ アップロード完了！")
        print(f"=" * 70)
        print(f"\nアップロード結果:")
        print(f"  - ヘッダー: {len(headers)}列")
        print(f"  - データ: {len(data_rows)}問")
        print(f"\nスプレッドシートURL:")
        print(f"  https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ アップロードエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
