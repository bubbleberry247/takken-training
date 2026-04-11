# 選択肢画像表示機能 実装ガイド

## 概要
数式などテキストで正確に表示できない選択肢を画像で表示する機能を実装します。

## 修正済み
- ✅ CSV: `choiceImageUrl` カラム追加
- ✅ R5gakkaA-020: 選択肢画像設定（imageUrlクリア）
- ✅ R6gakkaA-005: 選択肢画像設定（問題図は維持）

## 必要な修正

### 1. db.gs の修正

**ファイル**: `src/db.gs`
**行**: 17-25

**修正前**:
```javascript
HEADERS[SHEETS.QuestionBank] = [
  'qId', 'segmentId', 'type', 'difficulty',
  'tag1', 'tag2', 'tag3', 'lawTag',
  'revisionFlag', 'conceptId', 'variantGroupId', 'source_ref',
  'imageUrl',
  'stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
  'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
  'correct', 'explainShort', 'explainLong', 'status', 'updatedAt'
];
```

**修正後**:
```javascript
HEADERS[SHEETS.QuestionBank] = [
  'qId', 'segmentId', 'type', 'difficulty',
  'tag1', 'tag2', 'tag3', 'lawTag',
  'revisionFlag', 'conceptId', 'variantGroupId', 'source_ref',
  'imageUrl', 'choiceImageUrl',  // ← choiceImageUrl を追加
  'stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
  'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
  'correct', 'explainShort', 'explainLong', 'status', 'updatedAt'
];
```

### 2. logic.gs の修正

**ファイル**: `src/logic.gs`
**関数**: `buildQuestionForUser_`
**行**: 560-571

**修正前**:
```javascript
var choices = [
  { key: 'A', text: q.choiceA },
  { key: 'B', text: q.choiceB },
  { key: 'C', text: q.choiceC },
  { key: 'D', text: q.choiceD }
];
if (!isBlank_(q.choiceE)) {
  choices.push({ key: 'E', text: q.choiceE });
}
return {
  qId: q.qId,
  stem: q.stem,
  choices: choices,
```

**修正後**:
```javascript
var choiceImageUrl = String(q.choiceImageUrl || '').trim();
var choices = [
  { key: 'A', text: q.choiceA },
  { key: 'B', text: q.choiceB },
  { key: 'C', text: q.choiceC },
  { key: 'D', text: q.choiceD }
];
if (!isBlank_(q.choiceE)) {
  choices.push({ key: 'E', text: q.choiceE });
}
return {
  qId: q.qId,
  stem: q.stem,
  choices: choices,
  choiceImageUrl: choiceImageUrl,  // ← 追加
```

### 3. index.html の修正

**ファイル**: `src/index.html`

#### 修正箇所1: 診断テスト表示（約2135-2141行）

**修正前**:
```javascript
const correctBadge = isChoiceCorrect ? '<span class="chosen-badge ok">正解<\span>' : '';
const chosenBadge = isChosen ? '<span class="chosen-badge ' + (isChoiceCorrect ? 'ok' : 'ng') + '">あなたの解答</span>' : '';
return '<div class="' + cls + '">' +
  '<div class="choice-header">' + icon + '<span class="choice-label">選択肢' + escapeHtml(num) + '</span>' + correctBadge + chosenBadge + '</div>' +
  '<div>' + escapeHtml(c.text || '') + '</div>' +
  (explain ? '<div class="small">' + escapeHtml(explain) + '<\div>' : '') +
  '</div>';
```

**修正後**:
```javascript
const correctBadge = isChoiceCorrect ? '<span class="chosen-badge ok">正解<\span>' : '';
const chosenBadge = isChosen ? '<span class="chosen-badge ' + (isChoiceCorrect ? 'ok' : 'ng') + '">あなたの解答</span>' : '';

// 選択肢画像がある場合は画像を表示
let choiceContent;
if (q.choiceImageUrl) {
  choiceContent = '<img src="' + escapeHtml(q.choiceImageUrl) + '" style="max-width:100%;height:auto;display:block;margin:8px 0;" alt="選択肢画像">';
} else {
  choiceContent = '<div>' + escapeHtml(c.text || '') + '</div>';
}

return '<div class="' + cls + '">' +
  '<div class="choice-header">' + icon + '<span class="choice-label">選択肢' + escapeHtml(num) + '</span>' + correctBadge + chosenBadge + '</div>' +
  choiceContent +
  (explain ? '<div class="small">' + escapeHtml(explain) + '<\div>' : '') +
  '</div>';
```

#### 修正箇所2: 本試験表示（約2886-2892行）

**修正前**:
```javascript
const correctBadge = isChoiceCorrect ? '<span class="chosen-badge ok">正解<\span>' : '';
const chosenBadge = isChosen ? '<span class="chosen-badge ' + (isChoiceCorrect ? 'ok' : 'ng') + '">あなたの解答</span>' : '';
return '<div class="' + cls + '">' +
  '<div class="choice-header">' + icon + '<span class="choice-label">選択肢' + escapeHtml(num) + '</span>' + correctBadge + chosenBadge + '</div>' +
  '<div>' + escapeHtml(c.text || '') + '</div>' +
  (explain ? '<div class="small">' + escapeHtml(explain) + '<\div>' : '') +
  '</div>';
```

**修正後**:
```javascript
const correctBadge = isChoiceCorrect ? '<span class="chosen-badge ok">正解<\span>' : '';
const chosenBadge = isChosen ? '<span class="chosen-badge ' + (isChoiceCorrect ? 'ok' : 'ng') + '">あなたの解答</span>' : '';

// 選択肢画像がある場合は画像を表示
let choiceContent;
if (q.choiceImageUrl) {
  choiceContent = '<img src="' + escapeHtml(q.choiceImageUrl) + '" style="max-width:100%;height:auto;display:block;margin:8px 0;" alt="選択肢画像">';
} else {
  choiceContent = '<div>' + escapeHtml(c.text || '') + '</div>';
}

return '<div class="' + cls + '">' +
  '<div class="choice-header">' + icon + '<span class="choice-label">選択肢' + escapeHtml(num) + '</span>' + correctBadge + chosenBadge + '</div>' +
  choiceContent +
  (explain ? '<div class="small">' + escapeHtml(explain) + '<\div>' : '') +
  '</div>';
```

## テスト手順

1. **Google Sheetsにデータをインポート**
   - URL: https://docs.google.com/spreadsheets/d/1jj3AgZR2jAbgUIPtFRtjSfO0R0u5K_fiZyYQMwhEbM0/edit
   - QuestionBankシートを選択
   - ファイル → インポート → `questionbank_drive_import.csv`
   - インポート場所: **現在のシートを置き換える**

2. **GASコードを修正**
   - Apps Scriptエディタを開く
   - 上記の修正を適用
   - 保存してデプロイ

3. **動作確認**
   - テスト問題: R5gakkaA-020, R6gakkaA-005
   - 選択肢が画像で表示されることを確認

## 次のステップ

### R6gakkaA-003 (486行目) の数式問題対応

現在、選択肢が正しく表示されていない:
```
PL M = 2 PL,M = 3 PL,M = 6 PL,M = 9
```

**対応方法**:
1. 元のPDFから選択肢部分をキャプチャ
2. `R6gakkaA-003_choice.png` として保存
3. `images/` ディレクトリにアップロード
4. CSVの R6gakkaA-003 行の choiceImageUrl に URL を設定

## 注意事項

- 選択肢画像がある場合、choiceA〜Dのテキストは無視されます
- R5gakkaA-020のように問題図がない場合は imageUrl を空にします
- R6gakkaA-005のように問題図と選択肢画像が両方ある場合は両方設定します
