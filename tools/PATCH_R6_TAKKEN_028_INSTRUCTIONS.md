# R6takken-028 公式原典復元パッチ

## 現在の状態

- `data/r6_takken_028_release_ledger.csv` は公式原典監査済みの `approved`。
- 変更対象は `stem` 1列のみ。ア・イ・ウの3本文を復元し、公式原文にない後発制度の条件文を除去する。
- 公式正答は2＝現行key Bと一致。選択肢・正答・解説・画像・source_ref・statusは変更しない。
- canonical、生成import、GAS specはapproved after状態へ同期済み。
- 本番QuestionBankは未反映。read-only診断で本番固有baselineを確定済みだが、適用前の全行hash preflightは引き続き必須。

## source baselineとlive baseline

canonical planeのbefore→after、import planeのbefore→afterは、いずれもR6takken-028の`stem`だけであり、`explainLong`等を変更しない。canonical↔import間にはgeneratorの既存正規化による7列（`segmentId,type,difficulty,tag2,revisionFlag,variantGroupId,updatedAt`）の差があるが、これは本リリースの変更ではなく、テストで固定している。

本番のread-only診断receipt（`data/release-evidence/r6_q28_live_hash_diagnostic.json`、raw-byte SHA-256 `b73cffb1...10925`）で、30列中28列と旧stemはsource premiseに一致し、次の2差異だけを確認した。

- `explainLong`: 本番は空欄。今回の変更対象に加えず、空欄のまま保護する。
- `updatedAt`: 本番はDate型だが、表示日付はsourceの`2026-04-10`と一致。`updatedAt`に限定してAsia/Tokyoの`yyyy-MM-dd`でcanonical化し、セル自体は変更しない。pre/post/rollbackでDate型そのものも検査し、同じ表示値の文字列化を拒否する。

live semantic hashはbefore `07af011a...301e`、stem置換後 `76907447...b636`。source/import用hashとは別列で台帳管理し、generated GAS specはlive hashだけを本番preflightへ使用する。receiptはraw bytesを固定し、CRLF/BOM/1 byteの変更も拒否する。公式監査5証拠はOS差を除くcanonical hashとし、別ドメインの両者から作るcomposite approval hashが一致しない場合はfail-closedとする。receiptのcheckout bytesを保持するため`.gitattributes`で当該ファイルを`-text`固定する。

## 公式release ledgerの承認根拠

公式監査成果物から本文・PIIを除いた最小承認証拠 `data/release-evidence/r6_q28_official_approval.json` をrelease gateの正本として、次を固定した。releaseツールはclean checkoutに存在しない`work/`成果物へ依存しない。

1. `field_whitelist=stem`。
2. before／replacement stemと両payload hash。
3. canonical／runtimeのbefore／after全行hash。
4. RETIO公式PDF hash・問題ページ・公式正答表のkey B。
5. 旧監査成果物の集約hash、レビュー担当・日付（長文本文を再収録しない）。

official evidence hashはcheckout時の改行設定に依存しない。証拠をUTF-8として読み、先頭BOMを1個除去し、`CRLF`／`CR`を`LF`へ統一したBOMなしbytesをhash化し、固定ファイル名と`r6-q28-evidence-v1`のdomain prefixで集約する。live diagnostic receiptはこれと異なりraw bytes一致を要求する。

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

preflight/post-readは`explainLong=""`、`updatedAt`表示値`2026-04-10`、全30列live semantic hashを確認する。stem以外29列と非対象599行は不変でなければならない。

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
