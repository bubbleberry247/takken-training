# Claude for Chrome 説明文収集 - 引き継ぎ情報

作成日: 2026-02-16

## 📋 タスク概要

1級土木施工管理技士試験の問題データベースで、詳細説明文（explainA-D）が不足している問題について、過去問サイトから解説を収集してください。

## 🎯 収集対象

### 優先度1: 説明文完全欠落（31問）
**対象**: R6gakkaA-036〜066（31問）
- 原本Word文書に存在しない問題
- explainShort / explainA-D 全て空
- **最優先で収集が必要**

### 優先度2: 統合解説のみ（139問）
**対象**: R1-R3年度を中心に139問
- explainShortは存在（統合解説あり）
- explainA-Dが空（選択肢別説明なし）
- より詳細な学習体験のために収集推奨

## 📊 前回実績

### 収集済み（24問）
- **対象**: R2gakkaA-006〜032（一部）
- **形式**: Word文書（不足説明文.docx）
- **フォーマット**: Markdown表形式（9列）
- **品質基準**: 全て合格

### 使用サイト
- **過去問サイト**: https://1dobokusekou.kakomonn.com/
- **URL形式**: `https://1dobokusekou.kakomonn.com/questions/{ID番号}`

### ID番号の取得方法
CSV（`questionbank_drive_import.csv`）のid列を参照

## 📝 収集フォーマット

### Google Docs Markdown表形式
```
| qId | explainA | explainB | explainC | explainD | explainShort | explainLong | status | ID |
|-----|----------|----------|----------|----------|--------------|-------------|--------|-----|
| R6gakkaA-036 | 選択肢1の詳細説明... | 選択肢2の詳細説明... | 選択肢3の詳細説明... | 選択肢4の詳細説明... | 統合解説の要約（200文字程度）... | 統合解説の全文... | ✅ | 78591 |
```

### 各列の説明
- **qId**: 問題ID（例: R6gakkaA-036）
- **explainA-D**: 各選択肢の個別説明
  - 「適当です/不適当です/誤りです」等の判定を含む
  - 理由・根拠を含む完全な説明文
- **explainShort**: 統合解説の要約（最大200文字）
  - 問題のポイント・覚えるべき内容を簡潔に
- **explainLong**: 統合解説の全文
  - まとめ・補足情報を含む
- **status**: 収集状況（✅完了、⚠️要確認、❌未収集）
- **ID**: 問題のID番号（過去問サイトURL用）

## 🎯 品質基準

### 必須要件
✅ explainA-Dが全て揃っている
✅ 各選択肢に判定（適当/不適当）が明記されている
✅ 理由・根拠が含まれている
✅ 不正確な情報・推測が含まれていない

### 推奨要件
🟢 explainShortが簡潔で要点を押さえている
🟢 explainLongに補足・まとめがある
🟢 技術用語が正確に記載されている

## 📋 収集対象リスト

### 優先度1: R6gakkaA（31問）- ID範囲: 78591〜78626

| qId | ID | URL |
|-----|----|-----|
| R6gakkaA-036 | 78591 | https://1dobokusekou.kakomonn.com/questions/78591 |
| R6gakkaA-037 | 78592 | https://1dobokusekou.kakomonn.com/questions/78592 |
| R6gakkaA-038 | 78593 | https://1dobokusekou.kakomonn.com/questions/78593 |
| R6gakkaA-039 | 78594 | https://1dobokusekou.kakomonn.com/questions/78594 |
| R6gakkaA-040 | 78595 | https://1dobokusekou.kakomonn.com/questions/78595 |
| R6gakkaA-041 | 78596 | https://1dobokusekou.kakomonn.com/questions/78596 |
| R6gakkaA-042 | 78597 | https://1dobokusekou.kakomonn.com/questions/78597 |
| R6gakkaA-043 | 78598 | https://1dobokusekou.kakomonn.com/questions/78598 |
| R6gakkaA-044 | 78599 | https://1dobokusekou.kakomonn.com/questions/78599 |
| R6gakkaA-045 | 78600 | https://1dobokusekou.kakomonn.com/questions/78600 |
| R6gakkaA-046 | 78601 | https://1dobokusekou.kakomonn.com/questions/78601 |
| R6gakkaA-047 | 78602 | https://1dobokusekou.kakomonn.com/questions/78602 |
| R6gakkaA-048 | 78603 | https://1dobokusekou.kakomonn.com/questions/78603 |
| R6gakkaA-049 | 78604 | https://1dobokusekou.kakomonn.com/questions/78604 |
| R6gakkaA-050 | 78605 | https://1dobokusekou.kakomonn.com/questions/78605 |
| R6gakkaA-051 | 78606 | https://1dobokusekou.kakomonn.com/questions/78606 |
| R6gakkaA-052 | 78607 | https://1dobokusekou.kakomonn.com/questions/78607 |
| R6gakkaA-053 | 78608 | https://1dobokusekou.kakomonn.com/questions/78608 |
| R6gakkaA-054 | 78609 | https://1dobokusekou.kakomonn.com/questions/78609 |
| R6gakkaA-055 | 78610 | https://1dobokusekou.kakomonn.com/questions/78610 |
| R6gakkaA-056 | 78611 | https://1dobokusekou.kakomonn.com/questions/78611 |
| R6gakkaA-057 | 78612 | https://1dobokusekou.kakomonn.com/questions/78612 |
| R6gakkaA-058 | 78613 | https://1dobokusekou.kakomonn.com/questions/78613 |
| R6gakkaA-059 | 78614 | https://1dobokusekou.kakomonn.com/questions/78614 |
| R6gakkaA-060 | 78615 | https://1dobokusekou.kakomonn.com/questions/78615 |
| R6gakkaA-061 | 78616 | https://1dobokusekou.kakomonn.com/questions/78616 |
| R6gakkaA-062 | 78617 | https://1dobokusekou.kakomonn.com/questions/78617 |
| R6gakkaA-063 | 78618 | https://1dobokusekou.kakomonn.com/questions/78618 |
| R6gakkaA-064 | 78619 | https://1dobokusekou.kakomonn.com/questions/78619 |
| R6gakkaA-065 | 78620 | https://1dobokusekou.kakomonn.com/questions/78620 |
| R6gakkaA-066 | 78621 | https://1dobokusekou.kakomonn.com/questions/78621 |

### 優先度2: 統合解説のみ（139問）
※ 優先度1完了後に対応

主な対象年度：
- R1gakkaA: 12問（050-061）
- R2gakkaA: 24問（022, 028, 033-061）
- R2gakkaB: 29問（001-035）
- R3gakkaA: 45問（001-061）
- R3gakkaB: 27問（001-035）
- その他: 2問

詳細リストは別途提供

## 🔄 統合手順

### Claude Code側での処理
1. Google Docsから収集データを取得
2. `merge_explanations_from_docx.py`実行
3. CSV統合（バックアップ自動作成）
4. Google Sheetsインポート
5. Webアプリ動作確認

### 前回の統合実績
- **収集数**: 24問
- **統合成功**: 24問 (100%)
- **所要時間**: 約10分（Claude for Chrome作業）

## 📌 注意事項

### 収集時の注意
1. **選択肢番号の対応確認**
   - 過去問サイトの選択肢1→explainA
   - 過去問サイトの選択肢2→explainB
   - 過去問サイトの選択肢3→explainC
   - 過去問サイトの選択肢4→explainD

2. **判定の明記**
   - 「適当です」「不適当です」「誤りです」等を必ず含める

3. **特殊文字の扱い**
   - パイプ文字 `|` は表の区切りなので、説明文内では使用しない
   - 改行は半角スペースに置き換え

4. **品質確認**
   - 各問題で必ずexplainA-Dの4つ全てが揃っているか確認
   - 空欄・「不明」・「?」等は不可

### サイトが使えない場合
- R5gakkaA-057は原本欠番のため、過去問サイトにも存在しない可能性
- その場合は status列に「❌原本欠番」と記載

## 📊 期待される成果

### 優先度1完了時（31問収集）
- カバレッジ: 72.4% → **77.0%** (+4.6%)
- 説明文完全欠落: 32問 → **1問**（R5gakkaA-057のみ）

### 優先度2完了時（139問収集）
- カバレッジ: 77.0% → **92.4%** (+15.4%)
- 統合解説のみ: 139問 → **0問**

---

**関連ファイル**:
- CSV: `C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv`
- 統合スクリプト: `merge_explanations_from_docx.py`
- 前回実績: `不足説明文.docx`（24問）
