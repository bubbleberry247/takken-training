# ユーザー管理・権限運用ガイド

## 概要
- Google Workspace ログインを前提に、本人/上長/管理者の権限を管理します。
- 上長は「集計のみ」を閲覧できます（個別の受験履歴・回答内容は非表示）。
- 権限の正本は DB スプレッドシートの `UserAccess` シートです。

## 事前設定（必須）
1. Apps Script の「サービス」で **Admin Directory API** を有効化
2. Google Cloud Console でも **Admin SDK** を有効化
3. Webアプリの実行ユーザーは `USER_ACCESSING` で動作

## 役割（role）
- `user` : 本人の進捗のみ
- `manager` : 本人 + 直属部下の集計
- `admin` : 本人 + 直属部下の集計 + ユーザー管理

## UserAccess シートの列
`email, role, managerEmail, active, updatedAt`

- **email**: Google Workspace のメール
- **role**: `user` / `manager` / `admin`
- **managerEmail**: 直属上長のメール（user のみ必須）
- **active**: `true` / `false`
- **updatedAt**: 更新日時（自動で上書き）

## 一括登録（CSV）
### フォーマット
```
email,role,managerEmail,active
manager@company.co.jp,manager,,true
staff1@company.co.jp,user,manager@company.co.jp,true
staff2@company.co.jp,user,manager@company.co.jp,true
```

### 手順
1. Admin画面の「ユーザーCSV一括登録」に貼り付け
2. 「ユーザーCSV一括登録」ボタンをクリック
3. 「ユーザー一覧更新」で反映を確認

## 画面操作
- **ユーザー一覧更新**: `UserAccess` を読み込み
- **ユーザー行を追加**: UI上で手動追加
- **ユーザー権限を保存**: UIの入力内容を一括保存
- **ユーザーCSV一括登録**: CSVから一括登録

## 表示ルール
- **本人**: 自分の KPI / 週間推移 / 受験履歴
- **上長**: チーム進捗（メンバー別の集計のみ）
- **管理者**: 上長と同じ + ユーザー管理UI

## よくあるエラー
- 「ログインが必要です」: Workspaceログインが取得できていない
- 「管理者権限が必要です」: role が admin になっていない
- 「このユーザーは無効です」: active が false

## 推奨運用
- 管理者のみが `UserAccess` を更新する
- 退職/異動時は **active=false** で停止
- 上長変更時は **managerEmail** を更新
