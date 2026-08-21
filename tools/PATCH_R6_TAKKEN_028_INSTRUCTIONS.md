# R6takken-028 公式原典復元パッチ

## 現在の状態

- `data/r6_takken_028_release_ledger.csv` は公式原典監査済みの `approved`。
- 変更対象は `stem` 1列のみ。ア・イ・ウの3本文を復元し、公式原文にない後発制度の条件文を除去する。
- 公式正答は2＝現行key Bと一致。選択肢・正答・解説・画像・source_ref・statusは変更しない。
- canonical、生成import、GAS specはapproved after状態へ同期済み。
- 本番QuestionBankは未反映。direct live row export未実施のため、適用前の全行hash preflightが必須。

## 公式release ledgerの承認根拠

`work/statement-label-audit-20260821/` の公式監査成果物を正本として、次を固定した。

1. `field_whitelist=stem`。
2. before／replacement stemと両payload hash。
3. canonical／runtimeのbefore／after全行hash。
4. RETIO公式PDF hash・問題ページ・公式正答表のkey B。
5. 監査builder・release ledger・source manifest・work-only payload・summaryの集約evidence hash。

evidence hashはcheckout時の改行設定に依存しない。各証拠をUTF-8として読み、先頭BOMを1個除去し、`CRLF`／`CR`を`LF`へ統一したBOMなしbytesを個別hash化する。固定ファイル名と個別hashを固定順で集約し、`r6-q28-evidence-v1`のdomain prefix付きで最終hashを作る。

`release_status=approved` はdry-run可能を意味し、本番反映済みを意味しない。

## 正本・生成物同期

監査成果物からrelease台帳を再検証し、specを再生成する手順は次のとおり。

```text
python tools/r6_takken_028_release.py --approve-from-work-ledger
python tools/r6_takken_028_release.py --generate
python tools/r6_takken_028_release.py --apply-source
python tools/build_takken_import_csv.py
python tools/build_takken_import_csv.py --check
python tools/r6_takken_028_release.py --check
npm test
```

`--apply-source` はcanonicalの固定1 qId・whitelist列だけを更新し、before/after全行hash不一致なら書かない。既にafter状態ならno-op。この順序でcanonicalとimportをapproved after hashへ同期する。全量QuestionBank importは本件では使用しない。

## 本番dry-runと適用契約

1. deploy対象と本番DB IDを確認する。
2. `ADMIN_inspectTakkenR6028DryRun_()` で `matched=1`, `nonTargetCount=599` とlive全行hashを確認する。
3. `ADMIN_patchTakkenR6028DryRun_()` で `matched=1`, `wouldUpdate=1`, `nonTargetCount=599` を確認する。
4. 受講を止めた保守時間に `TAKKEN_R6_028_MAINTENANCE_WINDOW=OPEN` を設定する。
5. `ADMIN_applyTakkenR6028_()` を1回だけ実行する。
6. receipt、backup、post reread、strict cache invalidation、公開画面を確認し、保守propertyを閉じる。

QuestionBank書込みは、固定whitelistの`stem` 1セルだけを1回のAdvanced Sheets `spreadsheets.batchUpdate`（`updateCells`）で更新する。SpreadsheetApp逐次書込みや全量importへのfallbackはない。

## 停止条件

- release ledgerがapprovedでない、承認payload／hash／reviewerが欠ける。
- 600行／固定1 qId／599非対象でない、qIdが重複する。
- liveのexpected-before全行hashまたは個別before値が違う。
- whitelist外列、変更のない列、canonical/importの状態不一致がある。
- backup後に全体・非対象・行順・target行位置が変わる。
- DB_SPREADSHEET_ID／Spreadsheet objectが変わる。
- 保守時間外、Advanced Sheets API利用不可、応答不明、partial、strict cache失敗。

ScriptLockはGAS実行同士だけを止め、手動のSheet編集は止めない。API直前の最終再読から応答まで外部編集がないことは保守時間で保証する。行追加・削除・並替えを行わない。

## ロールバック

適用後の全体／非対象／行順hashがbackupのpost baselineと完全一致する場合だけ実行する。

```text
ADMIN_rollbackLatestTakkenR6028DryRun_()
ADMIN_rollbackLatestTakkenR6028_()
```

不一致・partial・応答不明では再実行せず、backupとQuestionBankを人手確認する。

## ローカル検証

```text
python tools/test_r6_takken_028_release.py
node tools/test_r6_takken_028_patch.mjs
npm test
```

公式内容の承認とローカル正本同期は完了している。本番データ更新、deploy、公開画面確認は完了していない。
