# 宅建士 R3 問38 局所パッチ運用手順

対象は、令和3年・問38の固定2件だけです。

- `R3atakken-038`
- `R3btakken-038`

全量CSVインポート、QuestionBankシートのクリア、公開Web API、画面操作は使用しません。QuestionBankへの書込みは、Google Sheets Advanced Service v4 の `Spreadsheets.batchUpdate` による、`stem`列限定の完全一致 find/replace 2件だけです。行番号を指定するフォールバックはありません。

## 事前条件と停止条件

1. 対象GASプロジェクトと `DB_SPREADSHEET_ID` が宅建士本番の組合せであることを確認する。別サイト・別DBなら停止する。
2. `src/appsscript.json` の Advanced Service 設定を反映し、GASプロジェクトで **Google Sheets API** と **Advanced Google services: Sheets API v4** を有効化する。どちらかが利用できない場合は、applyせず停止する。`SpreadsheetApp` の逐次セル更新への代替は実装していない。
3. 受講者がQuestionBankを編集しない短いメンテナンス時間を確保し、Script Properties に次を一時設定する。

```text
TAKKEN_R3Q38_MAINTENANCE_WINDOW=OPEN
```

適用・ロールバック完了後、直ちに値を削除するか `CLOSED` に戻す。dry-runにはこの設定は不要です。

次のいずれかに該当したら、書込みをせず停止します。

- 全QuestionBankのqIdが一意でない、空qIdがある、ヘッダー／列数が一致しない
- 対象2件が見つからない、対象が2件以外、または対象qIdが重複している
- 変更前stemのSHA-256が固定期待値と一致しない
- 変更前stemの「ア・イ・ウ・エ」マーカーが各0件でない
- 変更前stemがstem列全体で完全一致・部分一致とも1件でない
- 変更後stemがstem列のどこかに既に存在する、または部分文字列として存在する
- 同一の旧stem／新stemが固定2件の中で重複する
- backup後の再読込で、qId集合または全行ハッシュが変わった
- Advanced Sheets Serviceが利用できない、またはAPI応答の `occurrencesChanged` が各1でない
- 読み込んだSpreadsheet objectの`getId()`がplanの`DB_SPREADSHEET_ID`と一致しない、または実行中にobject／IDが変わる

## GASエディタでの実行入口

引数付き式はGASエディタのRunボタンから直接実行できないため、引数なしの private wrapper を使用します。公開RPCやUIには追加していません。

### 1. dry-run（必須）

```javascript
ADMIN_patchTakkenR3Q38DryRun_()
```

Loggerに、本文・選択肢を含めないマスク済みのqId、ハッシュ、件数だけが出ます。`matched=2`、`wouldUpdate=2`、全qId一意、非対象件数598を確認してください。dry-runはbackup sheetもQuestionBankも変更しません。

### 2. 本番適用

dry-runの結果、DB、対象qId、変更承認を確認し、メンテナンス時間中に次を1回だけ実行します。

```javascript
ADMIN_applyTakkenR3Q38_()
```

内部処理は次の順序です。

1. ScriptLockを取得する。
2. QuestionBank全行のqId・行ハッシュを読み、固定2件の全列を `_QuestionBankPatchBackup` へ保存する。source row numberは監査証跡であり、復元のキーには使わない。
3. backup sheetを再読込し、2件のqId、DB_SPREADSHEET_ID、before row hash、全体／非対象のbefore inventory hash、全列データが保存済みであることを検証する。検証に失敗したらQuestionBankを書かず停止する。
4. backup後にQuestionBankを再読込し、qId集合・全行ハッシュ・対象old hashが変わっていないことを確認する。行の並替えだけは許容する。
5. ScriptLockを保持したまま、同一Spreadsheet object／IDをAPI直前まで再検証する。`stem`列だけを対象範囲とする2件の完全一致 find/replaceを、planに保存したDB IDを固定して単一のSheets `batchUpdate`で送信する。各レスポンスの `occurrencesChanged` は必ず1でなければ失敗扱いにする。
6. `invalidateQuestionsCache_({strict:true})`を通じて、従来消えていなかったscript-scopeの`_questionsCache`と`_questionsCacheTs`を無効化する。共有`questions_version`の書込み失敗は握りつぶさず、applyを失敗扱いにしてrollback／manual reviewへ進める。通常のread pathではCacheService一時障害を許容してシート読込を継続する。
7. QuestionBankを再読込し、全qId一意、targetのnew/old出現数、対象行のstem以外、正答・選択肢・画像等、非対象全行が期待どおりであることを検証する。
8. apply後の全体／非対象inventory hashをbackupへ保存し、backup状態を`applied`に更新し、qIdとハッシュのみの結果をLoggerへ出す。

## 応答不明・強制終了・部分適用時

API呼出し後にタイムアウト、ブラウザ終了、GASの応答不明が起きても、すぐにapplyを再実行しないでください。まずmaintenance windowを維持し、同じwrapperのdry-runまたはbackup/statusとQuestionBankの状態を確認します。

- 全targetがoldで、事前状態の全行不変を検証できる場合：`not_applied`。再適用は承認後に行う。
- 全targetがnewで、対象・非対象の事後状態を検証できる場合：exactなnew→old 2件batchで自動rollbackを試み、復元検証が通った場合だけ`rolled_back`。
- backupに保存したapply後の全体／非対象inventory hashと現行QuestionBankが一致しない場合：post-apply driftとしてrollbackを開始せず停止する。
- 1件だけnew、old/new混在、qId集合変更、非対象変更、再読込不能：`partial`または`manual_review`。自動rollbackせず、顧客操作・データ差分を手動確認する。
- 同一Spreadsheet object／IDの検証失敗、strictな共有cache version更新失敗：applyを成功扱いにせず、状態を再確認する。

実際のSheets `batchUpdate`は単一リクエストの原子性を期待していますが、応答不明を成功と推定しないため、この状態分類を残しています。

## ロールバック

最新の`applied`パッチを戻す場合も、まずdry-runを実行します。

```javascript
ADMIN_rollbackLatestTakkenR3Q38DryRun_()
ADMIN_rollbackLatestTakkenR3Q38_()
```

明示的なpatchIdを使う場合は、引数付き関数をGASエディタのコンソール等で実行するのではなく、コードレビュー済みの管理作業として次のprivate coreを使用します。

```javascript
ADMIN_rollbackTakkenR3Q38Stems_({patchId: '実行結果のpatchId', dryRun: true})
ADMIN_rollbackTakkenR3Q38Stems_({patchId: '実行結果のpatchId', apply: true})
```

ロールバックもqIdで対象を再検索し、DB_SPREADSHEET_ID、backupのapply後全体／非対象inventory hash、newの完全一致・非対象全行不変を検証したうえで、stem列限定のnew→old 2件batchを送信します。後から対象の他列や非対象行に変更が入っている場合は停止します。失敗時はbackupを`rollback_failed`にし、手動確認が必要です。

## 運用後の画面確認

GASの結果だけでは本番公開の完了とは扱いません。実行結果、patchId、backup状態、再読込検証を保存した後、宅建士サイトで次を確認します。

- 年度別過去問の令和3年・問38（午前・午後）の問題文に「ア・イ・ウ・エ」が表示される
- 該当するミニテストでも同じ項目表示になる
- 選択肢・正答・解説・画像が変わっていない

実画面確認と本番GAS実行権限が未取得の間は、顧客へ「本番反映済み」と報告しません。

## ローカルテスト

```bash
node tools/test_patch_r3_q38.mjs
npm test
```

テストは、dry-run、Advanced Service manifest、行並替え競合、完全一致のoccurrences契約、duplicate old、new先行、partial応答、rollback、rollback failure、wrapper、DB identity、Spreadsheet object TOCTOU、apply後inventory drift、別Web実行インスタンスをまたぐversion-aware cache、strict cache invalidation failure、サービス未提供時fail-closedを検証します。

## 変更ファイルと本番前ブロッカー

- `src/patchR3Q38.gs`
- `src/appsscript.json`
- `tools/test_patch_r3_q38.mjs`
- `tools/PATCH_R3_Q38_INSTRUCTIONS.md`
- `tools/IMPORT_INSTRUCTIONS.md`（全量importを使わない注意書き）

backupの状態列は`patchStatus`（QuestionBankの保存列`status`とは別名）です。この実装・ローカルテストだけでは、実際の本番DBに書き込まれたこと、GASデプロイが公開版に反映されたこと、実画面で確認できたことは証明できません。本番プロジェクトの権限、Sheets API有効化、コードレビュー、clasp push／デプロイ、GAS結果、画面確認が残る手動工程です。
