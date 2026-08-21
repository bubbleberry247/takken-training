# 宅建士・設問内ラベル欠落51問 局所パッチ運用手順

対象は、公式原典照合で `confirmed_missing` となった固定51問です。正本台帳は `data/statement_label_corrections.csv` です。

- `R6takken-028` は `blocked` のため対象外
- `R3atakken-038`／`R3btakken-038` は既存のQ38パッチ対象のため、このパッチでは再更新しない
- 変更対象は `stem` 列だけ。選択肢、正答、解説、画像、source_ref、他の行は変更しない
- 台帳には変更前・変更後SHA-256、公式PDF URL／SHA-256／ページ、ラベル順、挿入位置を保持する

## 正本同期

canonical sourceと投入CSVの同期は、次で確認できます。

```text
python tools/apply_statement_label_corrections.py
python tools/build_takken_import_csv.py --check
```

canonical sourceを台帳の51件へ反映する作業は、承認済みqIdを明示した場合だけ行います。通常の再生成は次の順序です。

```text
python tools/apply_statement_label_corrections.py --apply --expected-target-count 51 --approve-qids <台帳51qIdのカンマ区切り>
python tools/build_takken_import_csv.py
python tools/build_takken_import_csv.py --check
```

sourceページのキャッシュから台帳を再生成する場合は `tools/build_statement_label_ledger.py`、GASの固定spec配列を再生成する場合は `tools/generate_statement_label_patch_gs.py` を使用します。再生成時も公式CSVの `confirmed_missing=51`、blocked除外、Q38除外を満たさなければ停止します。

## GAS dry-runと本番適用

`src/appsscript.json` のGoogle Sheets API v4 Advanced Serviceと、GCP側Sheets APIを有効化したうえで、公開RPCやUIではなくGASエディタのprivate wrapperを使用します。

1. `ADMIN_patchTakkenStatementLabelsDryRun_()`
2. Loggerで `matched=51`、`wouldUpdate=51`、`nonTargetCount=549` を確認
3. 承認済みメンテナンス時間にScript Propertiesへ次を一時設定

```text
TAKKEN_STATEMENT_LABEL_PATCH_MAINTENANCE_WINDOW=OPEN
```

4. `ADMIN_applyTakkenStatementLabels_()`
5. 完了後、maintenance propertyを`CLOSED`または削除

内部ではScriptLock、全51行の全列backup、DB ID／Spreadsheet object固定検証、qId／行順／全体／非対象ハッシュ検証、stem列限定の51件atomic `batchUpdate`、`occurrencesChanged=1`全件検証、strict cache version read-after-write、post rereadを行います。`findReplace`は`range`指定のみで、`allSheets`は指定しません。

## 停止条件とロールバック

次の場合は成功扱いにしません。

- qIdの空欄・重複・600行以外・51件以外
- blockedまたはQ38 qIdの混入
- 変更前／変更後ハッシュ不一致
- 旧stemの重複、変更後stemの先行存在、0件／複数件のAPI応答
- backup後の行順・qId・全列ハッシュ変更
- DB ID／Spreadsheet objectの変更
- Sheets API利用不可、partial応答、strict cache invalidation失敗

応答不明・partial・非対象変更では再実行せず、backupとQuestionBankを確認します。適用後の完全一致状態で、かつbackupの事後全体／非対象／行順ハッシュが現行と一致する場合だけ、次のdry-run→applyでロールバックできます。

```text
ADMIN_rollbackLatestTakkenStatementLabelsDryRun_()
ADMIN_rollbackLatestTakkenStatementLabels_()
```

ローカル契約テスト：

```text
node tools/test_statement_label_patch.mjs
npm test
```

この実装とローカルテストだけでは、本番DBへの反映、GAS公開版へのdeploy、実画面確認は完了扱いにしません。
