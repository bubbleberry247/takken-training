# 模試/演習 設計再整理（一次検定・本番フォーマット準拠）

## 0. 前提・スコープ
- 対象試験: **1級施工管理技士 一次検定**
- 問題は**ユーザー提供**（AI生成ではない）
- 本番フォーマットに寄せる（No範囲/必答・選択/4肢・5肢/時間）
- 模試は **R7相当 / R6相当 / R5相当の3本**（固定セット）
- **No.51–60は必答・5肢択一**（本番フォーマットに存在）

## 1. 設計の核（絶対にズレない軸）
1) **フォーマット（Blueprint）とコンテンツ（Question）を完全分離**  
2) **“本番っぽさ”は体験で作る**（タイマー強制・マークシートUI・選択数制約・見直しフラグ・提出フロー）  
3) **模試は固定セット（freeze）**として再現性を担保  
4) **品質担保を仕様化**（draft / reviewed / published）

## 2. 試験フォーマット（Blueprint）
### 2.1 標準テンプレ
- AM: **No.1–44 / 150分**
- PM: **No.45–72 / 120分**
- **No.51–60：必答・5肢択一**

### 2.2 客先要件の3分割（年×3区分）
Blueprintを増やすだけで同じエンジンに乗せる。
- BP_AM_IROHA（No.1–20）
- BP_AM_NIHOHE（No.21–44）
- BP_PM_IROHA（No.45–72）

## 3. データモデル（Sheets）

### 3.1 Questions（提供された問題を格納）
| col | name | type | note |
|---|---|---|---|
| A | questionVersionId | string | Q123_v3（immutable） |
| B | baseQuestionId | string | Q123 |
| C | version | number | 3 |
| D | choiceCount | number | 4 or 5 |
| E | stem | text | 設問 |
| F-J | opt1..opt5 | text | 5択はopt5使用 |
| K | correct | number | 1..5 |
| L | explanation | text | 解説 |
| M | tags | text | 工程;品質;安全 |
| N | loId | text | 論点ID |
| O | sourceRef | text | 例: 令和7年（2025年） 問1（午前 イ 問1） |
| P | status | enum | draft/reviewed/published |
| Q | updatedAt | datetime |  |

**ルール**
- 出題対象は **publishedのみ**
- 修正は新バージョン追加（過去採点が変わらない）

### 3.2 ExamBlueprints
| col | name | example |
|---|---|---|
| A | blueprintId | BP_PM_FULL |
| B | part | AM / PM |
| C | durationMin | 150 / 120 |
| D | selectionMode | STRICT / REAL |
| E | uiStyleId | STYLE_BOOKLET_01 |
| F | instructionTemplateId | INST_AM_01 |

### 3.3 ExamSectionRules（超重要）
| col | name | example | note |
|---|---|---|---|
| A | blueprintId | BP_PM_FULL |  |
| B | sectionId | PM_RO |  |
| C | label | 午後ロ | UI表示 |
| D | noFrom | 51 |  |
| E | noTo | 60 |  |
| F | ruleType | ALL / PICK |  |
| G | pickN | 8 | PICKのみ |
| H | choiceCount | 5 | **No.51–60は必ず5** |
| I | note | 応用能力 |  |

### 3.4 ExamSets（模試の凍結）
| col | name | example |
|---|---|---|
| A | examSetId | MOCK_R7_PM_v1 |
| B | mockId | MOCK_R7 |
| C | part | PM |
| D | blueprintId | BP_PM_FULL |
| E | questionMapJson | {"45":"Q1_v1",...} |
| F | createdAt | datetime |
| G | version | v1 |
| H | published | TRUE |

**ルール**
- questionMapJsonは固定（再現性）
- 改訂はv2を新規追加

### 3.5 MockExams
| col | name | example |
|---|---|---|
| A | mockId | MOCK_R7 |
| B | title | R7相当 模擬試験 |
| C | amExamSetId | MOCK_R7_AM_v1 |
| D | pmExamSetId | MOCK_R7_PM_v1 |
| E | published | TRUE |

### 3.6 Attempts
| col | name | note |
|---|---|---|
| attemptId | UUID |  |
| email | string | Session.getActiveUser() |
| mockId | string | MOCK_R7 |
| part | AM/PM |  |
| examSetId | string |  |
| startedAt | datetime | server |
| deadlineAt | datetime | server |
| submittedAt | datetime |  |
| status | enum | in_progress/submitted/expired |
| answersJson | text | {"45":2,"46":null,...} |
| scoreTotal | number |  |
| scoreBySectionJson | text |  |
| scoreByTagJson | text |  |

**設計意図**
- answersJsonを1行に集約（GAS/Sheets負荷対策）

## 4. 体験設計（UI/UX）
### 4.1 画面遷移
Home → 模試開始 → Exam Runner → 提出確認 → 結果 → 復習

### 4.2 Exam Runner必須要素
- TimerBar（固定）
- MarkSheet（No一覧 + バブル）
  - No.51–60は5択バブル
- BookletView（冊子風）
  - A4比率、余白、ページ番号風
  - Phase 1は「設問リスト」でもOK

## 5. PICK（選択問題）仕様
### 5.1 STRICT（推奨）
- pickN到達で新規回答不可
- 解除で枠を空ける

### 5.2 REAL（後から追加）
- 超過回答OK、常時警告
- 採点は「No昇順でpickN」

## 6. タイマー & 自動保存
### 6.1 仕様
- apiStartAttemptで startedAt/deadlineAt確定
- clientはdeadlineAtまでの残り時間表示
- apiSaveProgress / apiSubmitAttempt は期限チェック

### 6.2 自動保存
- 10〜30秒ごとに answersJson 保存
- 失敗時はlocalStorageキューに溜めて再送
- UIに保存状態表示

## 7. API仕様（最小）
### 7.1 apiListMocks()
```
{ "mocks": [
  {"mockId":"MOCK_R7","title":"R7相当 模擬試験","published":true},
  {"mockId":"MOCK_R6","title":"R6相当 模擬試験","published":true},
  {"mockId":"MOCK_R5","title":"R5相当 模擬試験","published":true}
] }
```

### 7.2 apiStartAttempt(mockId, part)
```
{
  "attemptId":"UUID",
  "examSetId":"MOCK_R7_PM_v1",
  "deadlineAt":"2026-01-30T12:00:00+09:00",
  "blueprint": { "durationMin":120, "selectionMode":"STRICT" },
  "sectionRules":[
    {"noFrom":45,"noTo":50,"ruleType":"ALL","choiceCount":4},
    {"noFrom":51,"noTo":60,"ruleType":"ALL","choiceCount":5,"note":"応用能力"},
    {"noFrom":61,"noTo":72,"ruleType":"PICK","pickN":8,"choiceCount":4}
  ],
  "questions":[
    {"qNo":45,"questionVersionId":"Q1_v1","choiceCount":4,"stem":"...","options":["...","...","...","..."]},
    {"qNo":51,"questionVersionId":"Q99_v2","choiceCount":5,"stem":"...","options":["...","...","...","...","..."]}
  ]
}
```

### 7.3 apiSaveProgress(attemptId, answersJson, meta)
- answersJson例: `{"45":2,"46":null,"51":5}`
- metaは見直しフラグ等

### 7.4 apiSubmitAttempt(attemptId)
```
{
  "status":"submitted",
  "scoreTotal": 18,
  "scoreBySection":[
    {"label":"午後イ","correct":4,"answered":6},
    {"label":"午後ロ(応用能力)","correct":6,"answered":10},
    {"label":"午後ハ","correct":8,"answered":8}
  ],
  "weakTags":[
    {"tag":"安全","accuracy":0.42},
    {"tag":"品質","accuracy":0.50},
    {"tag":"工程","accuracy":0.55}
  ]
}
```

## 8. 採点ロジック
- ALL: 範囲内は全て採点対象
- PICK:
  - STRICT: UIで超過防止、サーバは異常値なら補正 or reject
  - REAL: No昇順でpickN採点

## 9. 見た目再現（段階戦略）
Phase 1: MarkSheet本番寄せ + A4比率の冊子風  
Phase 2: ページ分割、注意枠、No装飾強化  
Phase 3: ExamSet→冊子PDF生成

## 10. 実装分担（Codex / cowork）

### Codex（Backend/GAS）
- Sheetsスキーマ追加・既存統合
- Blueprint / SectionRules / ExamSet / MockExamsのAPI実装
- Start/Save/Submit/Scoring
- deadlineAt・期限チェック
- answersJson保存基盤
- 管理用: ExamSet凍結生成・Questions公開ステータス管理

**受け入れ条件**
- No.51–60が5択として出題・保存・採点される
- PICK制約がSTRICTで破綻しない
- 期限超過時の仕様どおりに動作する

### cowork（Frontend/UI）
- Home（模試3本＋午前/午後開始）
- Exam Runner（TimerBar + MarkSheet + BookletView）
- PICKカウンタ＆STRICT制約UI
- Autosaveキュー（localStorage）＋保存状態表示
- 結果画面（総合・セクション・弱点タグ）
- 紙面風CSS（A4比率・余白・ページ番号）

**受け入れ条件**
- MarkSheetが本番風に使える（4択/5択混在対応）
- 期限表示が正しく、0で自動提出できる
- STRICT超過防止がUIで保証される

## 11. デフォルト値（暫定）
- selectionMode: STRICT
- autosave: 15秒
- 期限超過: Save拒否 / Submit許可（expired）
- 模試セット: 固定（freeze）
- 出題対象: publishedのみ

## 12. 未確定（要決定）
- 期限超過時の扱い（Save拒否 / Submit許可でよいか）
- REALモード導入有無（Phase 2以降）
- 問題提供・更新フロー（reviewed→published）
