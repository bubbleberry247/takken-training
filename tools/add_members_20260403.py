#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026-04-03: 新規メンバー2名を土木・建築両アプリの UserAccess シートに追加する。
clasp認証情報を使用。重複チェック付き。
"""
import sys
import io
import json
from pathlib import Path
from datetime import datetime

import gspread
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.auth.transport.requests import Request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 設定
PROJECT_DIR = Path(__file__).parent.parent
CLASP_RC_FILE = PROJECT_DIR / '.clasprc.json'

DOBOKU_DB_ID = '1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0'
ARCHI_DB_ID = '1tesaYYXP7hsZFbq03irX_MNGvb_TZyeG609QNOvU6WU'

NEW_MEMBERS = [
    ['m.terada.tscg@gmail.com', 'user', '寺田 征弘'],
    ['t.masuhara.tscg@gmail.com', 'user', '増原 卓也'],
]


def get_credentials():
    if not CLASP_RC_FILE.exists():
        print(f'clasp認証情報が見つかりません: {CLASP_RC_FILE}')
        sys.exit(1)
    with open(CLASP_RC_FILE, 'r', encoding='utf-8') as f:
        clasp_data = json.load(f)
    token_data = clasp_data.get('token', {})
    clasp_scopes = token_data.get('scope', '').split(' ')
    creds = OAuthCredentials(
        token=token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=clasp_data.get('oauth2ClientSettings', {}).get('clientId'),
        client_secret=clasp_data.get('oauth2ClientSettings', {}).get('clientSecret'),
        scopes=clasp_scopes,
    )
    if creds.expired and creds.refresh_token:
        print('  トークンを更新中...')
        creds.refresh(Request())
    return creds


def add_members(gc, spreadsheet_id, app_name):
    print(f'\n--- {app_name} ---')
    ss = gc.open_by_key(spreadsheet_id)
    sh = ss.worksheet('UserAccess')

    existing_emails = set()
    records = sh.col_values(1)  # A列全体
    for email in records[1:]:   # ヘッダー除外
        if email:
            existing_emails.add(email.strip().lower())

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    added = 0
    skipped = 0

    for m in NEW_MEMBERS:
        email, role, name = m
        if email.strip().lower() in existing_emails:
            print(f'  スキップ（既存）: {email}')
            skipped += 1
            continue
        # [email, role, managerEmail, active, updatedAt, displayName]
        row = [email, role, '', 'TRUE', now, name]
        sh.append_row(row, value_input_option='USER_ENTERED')
        print(f'  追加: {email} ({name})')
        added += 1

    print(f'  結果: 追加 {added}名, スキップ {skipped}名')


def main():
    print('=' * 50)
    print('新規メンバー追加 (2026-04-03)')
    print('=' * 50)

    creds = get_credentials()
    gc = gspread.authorize(creds)

    add_members(gc, DOBOKU_DB_ID, '土木アプリ')
    add_members(gc, ARCHI_DB_ID, '建築アプリ')

    print('\n=== 完了 ===')


if __name__ == '__main__':
    main()
