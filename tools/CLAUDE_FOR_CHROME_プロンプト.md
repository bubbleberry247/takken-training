# Claude for Chrome 説明文収集プロンプト

以下のプロンプトをClaude for Chromeに渡してください。

---

## 📋 タスク

1級土木施工管理技士試験の過去問サイトから、R6年度学科A（問36〜66）の31問について、選択肢別の詳細説明文を収集してGoogle Docsのマークダウン表形式で整理してください。

## 🎯 作業内容

### 1. 各問題について以下を収集
過去問サイト: https://1dobokusekou.kakomonn.com/questions/{ID番号}

**収集する情報**:
1. **explainA**: 選択肢1の詳細説明
   - 判定（適当です/不適当です/誤りです）を含む
   - 理由・根拠を含む完全な説明文
2. **explainB**: 選択肢2の詳細説明
3. **explainC**: 選択肢3の詳細説明
4. **explainD**: 選択肢4の詳細説明
5. **explainShort**: 統合解説の要約（200文字程度）
   - 問題のポイント・覚えるべき内容を簡潔に
6. **explainLong**: 統合解説の全文
   - まとめ・補足情報を含む

### 2. Google Docsに以下の形式で記録

```
| qId | explainA | explainB | explainC | explainD | explainShort | explainLong | status | ID |
|-----|----------|----------|----------|----------|--------------|-------------|--------|-----|
```

**記入例**:
```
| R6gakkaA-036 | 適当です。○○は△△であり、××の基準を満たしています。 | 不適当です。○○は△△であるべきですが、この記述は××となっており誤りです。 | 適当です。○○に関する説明として正しい内容です。 | 適当です。○○の手順として適切です。 | この問題では○○に関する基準と手順を理解しているかが問われています。選択肢2の××に関する記述が誤りです。 | ○○に関する問題です。選択肢1は△△の基準、選択肢3は□□の手順、選択肢4は◇◇の管理について正しく述べています。選択肢2のみ、××の値が誤っており、正しくは△△です。現場での施工管理において、この基準値を正確に把握しておくことが重要です。 | ✅ | 78591 |
```

## 📝 収集対象（31問）

### R6gakkaA-036〜066

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

## ✅ 品質基準

### 必須要件（これらを満たさない場合は不合格）
- ✅ explainA、B、C、Dの**4つ全て**が揃っている
- ✅ 各選択肢に**判定**（適当です/不適当です/誤りです）が明記されている
- ✅ 各選択肢に**理由・根拠**が含まれている
- ✅ 推測や不正確な情報が含まれていない
- ✅ パイプ文字 `|` を説明文内で使用していない（表の区切りと混同するため）

### 推奨要件
- 🟢 explainShortは200文字程度で要点を簡潔にまとめている
- 🟢 explainLongに補足・まとめ・現場での注意点が含まれている
- 🟢 技術用語が正確に記載されている
- 🟢 数値・単位が正確に記載されている

## 📌 重要な注意事項

### 1. 選択肢番号の対応
- 過去問サイトの「選択肢1」→ **explainA**
- 過去問サイトの「選択肢2」→ **explainB**
- 過去問サイトの「選択肢3」→ **explainC**
- 過去問サイトの「選択肢4」→ **explainD**

### 2. テキスト整形
- 改行は**半角スペース**に置き換える
- パイプ文字 `|` は使用しない
- 全角スペースは半角スペースに統一

### 3. status列の記入
- 収集完了: `✅`
- 要確認（不明点あり）: `⚠️`
- サイトにない: `❌`

### 4. 作業の進め方
- **一度に全て作業せず**、10問ごとに区切って進めることを推奨
- 各区切りでGoogle Docsに記録して進捗を保存
- 疲れたら休憩を取る（精度が落ちるため）

## 📊 期待される成果

完了時点で以下が達成されます：
- ✅ R6年度学科A 問36〜66の詳細説明文が全て揃う
- ✅ データベースのカバレッジが 72.4% → 77.0% に向上
- ✅ 説明文完全欠落が 32問 → 1問に削減

## 🔄 完了後の連絡

作業完了後、以下をClaude Codeに報告してください：
1. Google DocsのURL
2. 収集完了問題数
3. 要確認（⚠️）の問題数
4. サイトにない（❌）問題があればその番号

Claude Code側で統合スクリプトを実行し、データベースに取り込みます。

---

## 補足情報

### 過去問サイトの構造
各問題ページには以下が含まれています：
- 問題文
- 選択肢1〜4
- 正解
- **解説**セクション
  - 各選択肢の個別説明（explainA-Dに対応）
  - 統合解説・まとめ（explainShort/Longに対応）

### Google Docsでの表作成
1. 新しいGoogle Docsを作成
2. 表のヘッダー行をコピー&ペースト
3. 各問題の情報を1行ずつ追加
4. 完了後、共有リンクを取得

お疲れ様です！品質の高いデータ収集をお願いします。
