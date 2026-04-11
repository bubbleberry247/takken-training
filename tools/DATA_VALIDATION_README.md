# データ整合性検証ツール

## 概要

`questionbank_drive_import.csv` の全682問に対してデータ整合性検証を実施するツールセットです。

## ツール一覧

### 1. check_integrity.py

データ整合性の詳細検証を実施します。

**検証項目**:
- 必須フィールドの欠落チェック (qId, segmentId, stem, correct)
- 選択肢数の統一確認 (4択: A-D, 5択: A-E)
- 年度・セグメント情報の検証 (qId/segmentIdの整合性)
- source_refの形式統一確認
- テキスト品質の検証（文字化け、異常な文字など）
- メタデータフィールドの検証 (type, difficulty, status)

**実行方法**:
```bash
cd tools
python check_integrity.py
```

**出力**:
- コンソールに検証結果サマリーを表示
- `integrity_check_report_{timestamp}.csv` にエラーレポートを出力

### 2. generate_summary_report.py

データ統計サマリーレポートを生成します。

**統計項目**:
- 全体統計（総問題数、セグメント数）
- 年度別問題数
- セグメント別問題数
- 選択肢タイプ別（4択/5択）
- 問題タイプ別（knowledge/application/comprehension）
- 難易度別（1-5）
- カテゴリー別（tag1）
- ステータス別（published/draft/archived）
- コンテンツ充実度（解説あり、画像あり）

**実行方法**:
```bash
cd tools
python generate_summary_report.py
```

**出力**:
- コンソールに統計レポートを表示

## 最新検証結果

### 検証日時: 2026-02-16 10:56:59

**検証結果サマリー**:
- ✅ 総データ数: 682問
- ✅ ユニークqId数: 682（重複なし）
- ✅ ERROR: 0件
- ✅ WARNING: 0件
- ✅ INFO: 0件

**セグメント別問題数**:
| セグメント | 問題数 |
|-----------|--------|
| R1gakkaA  | 61問   |
| R1gakkaB  | 35問   |
| R2gakkaA  | 61問   |
| R2gakkaB  | 35問   |
| R3gakkaA  | 61問   |
| R3gakkaB  | 35問   |
| R4gakkaA  | 61問   |
| R4gakkaB  | 35問   |
| R5gakkaA  | 61問   |
| R5gakkaB  | 35問   |
| R6gakkaA  | 66問   |
| R6gakkaB  | 35問   |
| R7gakkaA  | 66問   |
| R7gakkaB  | 35問   |

**コンテンツ充実度**:
- 解説あり: 321問 (47.1%)
- 問題画像あり: 71問 (10.4%)
- 選択肢画像あり: 2問 (0.3%)

## データ品質評価

### ✅ 優良項目
1. **完全性**: 全682問で必須フィールド（qId, segmentId, stem, correct）が揃っている
2. **一意性**: qIdの重複なし（全682問がユニーク）
3. **整合性**: segmentIdとqIdの関係が全問で正しい
4. **標準化**: 選択肢は全て4択で統一（一部組合せ問題を含む）

### 📊 改善推奨項目
1. **解説の充実**: 解説がない問題が361問（52.9%）存在
   - 推奨: explainShortまたはexplainLongの追加
2. **画像の追加**: 問題画像がない問題が611問（89.6%）
   - 推奨: 図表を含む問題への画像追加

### ℹ️ 参考情報
- 全問題が `knowledge` タイプ
- 全問題が難易度 `3`
- 全問題が `published` ステータス

## トラブルシューティング

### BOM付きCSVファイルの処理

CSVファイルにBOM（Byte Order Mark）が含まれている場合、`encoding='utf-8-sig'` を使用して読み込みます。

```python
with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
```

### 組合せ問題の検証

問題文に「組合せ」または「組み合わせ」が含まれる場合、選択肢が数字のみ（例: 1, 2, 3, 4）でも正常と判定されます。

## ファイル構成

```
tools/
├── check_integrity.py              # 整合性検証スクリプト
├── generate_summary_report.py      # 統計サマリー生成スクリプト
├── questionbank_drive_import.csv   # 検証対象データ（682問）
├── integrity_check_report_*.csv    # 検証レポート（自動生成）
└── DATA_VALIDATION_README.md       # このファイル
```

## 検証基準詳細

### 必須フィールド

以下のフィールドは空であってはならない:
- `qId`: 問題ID（形式: R{年度}gakka{A|B}-{3桁番号}）
- `segmentId`: セグメントID（qIdから導出）
- `stem`: 問題文
- `correct`: 正解（A, B, C, D, Eのいずれか）

### 選択肢の検証

- 4択問題: choiceA, choiceB, choiceC, choiceD が必須
- 5択問題: choiceA-D に加えて choiceE が必須
- correctフィールドと選択肢の整合性を確認

### qIdフォーマット

正規表現: `^R\d+gakka[AB]-\d{3}$`

例:
- ✅ `R1gakkaA-001`
- ✅ `R7gakkaB-035`
- ❌ `R1gakka-A-001` （ハイフンの位置が不正）
- ❌ `R1gakkaA-1` （番号が3桁でない）

### source_refフォーマット

正規表現: `^R\d+\s学科[AB]\sNo\.\d+$`

例:
- ✅ `R1 学科A No.1`
- ✅ `R7 学科B No.35`
- ❌ `R1学科ANo.1` （スペースがない）

## 更新履歴

- 2026-02-16: 初版リリース
  - check_integrity.py 作成
  - generate_summary_report.py 作成
  - 全682問の検証完了（ERROR 0件）
