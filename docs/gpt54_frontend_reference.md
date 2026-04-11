# GPT-5.4 Frontend Reference

2026年3月20日公開の OpenAI 公式記事
`Designing delightful frontends with GPT-5.4`
を、このリポジトリ向けに解釈したメモ。

元記事:
https://developers.openai.com/blog/designing-delightful-frontends-with-gpt-5-4

## この案件で使う前提

- 対象は LP ではなく、受験学習用の運用アプリ
- 実装基盤は GAS + `src/index.html` の Vanilla JS SPA
- 主利用環境はスマホ
- したがって、元記事の中でも `Apps` と `Utility Copy For Product UI` を優先する

## このアプリにそのまま効く原則

### 1. 画面の第一印象は「宣伝」ではなく「次の行動」

- Home の最上段はブランド演出より、今日やることを最短で理解できることを優先する
- 既存の `next-action-card` は方向性として良い
- ただし周辺に情報を詰め込みすぎると、記事でいう「dashboard-card mosaics」に寄る

この案件での解釈:
- 最上段は 1 つの主行動だけを強く出す
- その下に KPI / テスト一覧 / 弱点復習を置く
- Hero 的なコピーは増やさない

### 2. カードは「見た目の習慣」ではなく「操作の容器」にだけ使う

元記事では app UI に対して
`cards only when the card is the interaction`
を強く勧めている。

この案件での解釈:
- `next-action-card` は CTA を持つので維持してよい
- `test-card` も押せる単位なので成立する
- 逆に、情報を見せるだけの箱は線・余白・見出しで整理し、無理に全部カード化しない
- KPI は情報の比較が主目的なので、枠の主張を弱めてタイポグラフィで差を付ける

### 3. 文言は marketing copy ではなく utility copy

- 見出しは「何が見えるか」「何ができるか」を直接書く
- 抽象的な応援文や雰囲気コピーは増やさない
- ラベルだけでスキャンして意味が通ることを優先する

良い方向:
- `今日のテスト`
- `弱点から復習`
- `直近7日の受験`

避けたい方向:
- `合格に向けた最高の一歩`
- `未来の自分を変える学習体験`

### 4. 1 セクション 1 役割

- 最上段: 今日やること
- KPI: 現状把握
- テスト一覧: 実行
- 弱点復習: 補助導線
- 最近の受験: 振り返り

1 セクションの中で
「説明」「宣伝」「数値」「導線」を全部やらない。

### 5. 色数は絞る

元記事は
- 1 accent color を基本
- app UI に decorative gradients を持ち込みすぎない

を推奨している。

この案件での解釈:
- 基本アクセントは現行の青系で統一
- 警告や未完了だけ補助色を使う
- 通常の一覧や管理画面では、強いグラデーションを増やしすぎない
- グラデーションは「次の行動」など主役の 1 箇所に限定する

### 6. モバイルで安全に見えることを優先する

元記事では sticky/fixed UI の重なりを特に警戒している。

この案件での解釈:
- sticky header と tab の高さを前提に、初期表示で主 CTA が隠れないこと
- モーダル、ボタン、表、グラフが 390px 前後でも崩れないこと
- 動きは入れても 2-3 個まで。意味のあるものだけにする

## 現状コードへの当てはめ

### すでに合っている点

- `renderNextAction()` で「次の一手」を最上段に置いている
- `docs/ui_ux_redesign.md` でも行動誘導が主目的になっている
- モバイルファーストで組まれている

### 次に見直すと効く点

- `.card`, `.kpi-card`, `.test-card`, `.chart-card` など箱の表現がやや多い
- Home が「使える」だけでなく「すぐ判断できる」画面になるよう、装飾より情報優先に寄せる余地がある
- KPI と一覧系は、色面と枠よりタイポグラフィと余白で整理した方が元記事の方針に近い

## 次回 Codex / GPT に渡すためのプロンプト雛形

```text
このリポジトリの既存 UI を改善してください。
対象は landing page ではなく、受験学習用の operational app UI です。
GAS + src/index.html の既存構成を前提に、既存の機能と遷移は壊さないでください。

目的:
- ユーザーが Home を開いた瞬間に「今やること」が分かること
- KPI, テスト一覧, 弱点復習, 最近の受験を短時間でスキャンできること
- モバイルで押しやすく、PCでも間延びしないこと

Hard rules:
- marketing hero を作らない
- utility copy を使う
- 1 section 1 job
- cards are allowed only when they are the interaction container
- dashboard-card mosaics を避ける
- accent color は基本 1 色
- sticky header / tab が本文を隠さない
- 390px 前後と 1280px 前後の両方で崩さない

Visual direction:
- calm, dense, readable
- strong typography and spacing
- minimal chrome
- primary action first

Implementation constraints:
- src/index.html の既存 JS 構成を維持
- 大規模なフレームワーク移行はしない
- 既存の配色資産をベースにする

Verification:
- Home 初期表示で主 CTA がファーストビューに入る
- 各セクション見出しだけ読んでも意味が通る
- 不要なカード装飾を削っても意味が落ちない箇所は削る
```

## 実装前チェックリスト

- これは LP か app UI か
- 最上段はブランド訴求か、次の行動か
- そのカードは本当に押す対象か
- 見出しだけ読んで内容が分かるか
- 色の役割が増えすぎていないか
- sticky UI が本文を隠していないか
- 390px 幅で窮屈になっていないか

## 参照元

- OpenAI Developers Blog, `Designing delightful frontends with GPT-5.4`, 2026-03-20
- `docs/ui_ux_redesign.md`
- `src/index.html`
