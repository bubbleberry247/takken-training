# images/ — 問題画像

QuestionBank の `imageUrl` で参照する問題画像を格納するフォルダです。

[← リポジトリルートへ](../README.md)

## sekisan 画像
- 配置先: `images/sekisan/`
- ファイル名: `sekisan_<年度>_<問題番号>.png`
- 例: `sekisan_H25_043.png`

## 画像登録方法
1. `images/sekisan/` 内の画像を Google Drive フォルダへアップロード
2. Apps Script 側で `createImageFolder` または `getOrCreateImageFolder_()` により保存先を作成
3. `apiAdminLinkAllDriveImages` を実行して `QuestionBank.imageUrl` を Drive URL に更新

## 補足
- 完成版 CSV では、画像付き問題に `images/sekisan/...` のプレースホルダが入っている
- `src/sekisanConfig.gs` の変換ヘルパーで `qId` と画像ファイル名を相互変換できる
- 現在の sekisan 画像枚数は 108 枚
