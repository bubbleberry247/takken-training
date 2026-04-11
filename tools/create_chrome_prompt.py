# coding: utf-8
"""
不足している解説文を取得するためのClaude for Chromeプロンプトを生成
"""
import sys
import csv
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def create_prompt_for_missing_questions():
    """不足している3問のプロンプトを作成"""

    csv_path = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\questionbank_drive_import.csv")

    missing_qids = ['R6gakkaA-022', 'R6gakkaA-025', 'R6gakkaA-031']

    questions_data = {}

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['qId'] in missing_qids:
                questions_data[row['qId']] = {
                    'qId': row['qId'],
                    'source_ref': row['source_ref'],
                    'stem': row['stem'],
                    'choiceA': row['choiceA'],
                    'choiceB': row['choiceB'],
                    'choiceC': row['choiceC'],
                    'choiceD': row['choiceD'],
                    'correct': row['correct']
                }

    # プロンプトテンプレート
    prompt_template = """# 1級土木施工管理技士試験 解説文収集タスク

## 📌 目的
過去問サイト（https://1dobokusekou.kakomonn.com/）から、以下の問題の**詳細な解説文**を取得してください。

---

## 🎯 収集対象問題（3問）

{questions_list}

---

## 📝 収集方法

### ステップ1: 問題IDの特定
1. 過去問サイト（https://1dobokusekou.kakomonn.com/）を開く
2. 検索機能を使って、各問題の本文（stem）で検索
3. 該当する問題のページURLを確認
4. URLから問題ID（5桁の数字）を抽出
   - 例: `https://1dobokusekou.kakomonn.com/questions/78582` → ID: `78582`

### ステップ2: 解説文の収集
各問題ページから、以下の情報を抽出してください：

**収集する情報:**
- **問題文（stem）**: 確認用
- **選択肢A**: 内容と解説（「適当」or「不適当」+ 理由2-3文）
- **選択肢B**: 内容と解説（「適当」or「不適当」+ 理由2-3文）
- **選択肢C**: 内容と解説（「適当」or「不適当」+ 理由2-3文）
- **選択肢D**: 内容と解説（「適当」or「不適当」+ 理由2-3文）
- **正解**: どの選択肢が正解か
- **全体解説（explainShort）**: 問題全体の解説文（2-5文程度）

---

## 📤 出力フォーマット

以下のフォーマットで、各問題の解説を出力してください：

```
### R6gakkaA-022（問題ID: XXXXX）

**問題文:**
[問題文をここに]

**選択肢と解説:**

**A.** [選択肢Aの内容]
→ 【適当/不適当】[理由を2-3文で説明]

**B.** [選択肢Bの内容]
→ 【適当/不適当】[理由を2-3文で説明]

**C.** [選択肢Cの内容]
→ 【適当/不適当】[理由を2-3文で説明]

**D.** [選択肢Dの内容]
→ 【適当/不適当】[理由を2-3文で説明]

**正解:** [A/B/C/D]

**全体解説:**
[問題全体の解説を2-5文で]

---
```

## ⚠️ 注意事項

1. **解説の品質**: 各選択肢について、なぜ適当/不適当なのかを具体的に説明してください
2. **正確性**: 過去問サイトの情報をそのまま転記してください
3. **完全性**: すべての選択肢（A-D）の解説を必ず含めてください
4. **フォーマット**: 上記のフォーマットを厳守してください

---

よろしくお願いします！
"""

    # 問題リストを作成
    questions_list = []
    for idx, qid in enumerate(missing_qids, 1):
        if qid in questions_data:
            q = questions_data[qid]
            questions_list.append(f"""
### {idx}. {q['qId']} ({q['source_ref']})

**問題文:**
{q['stem']}

**選択肢:**
- A. {q['choiceA']}
- B. {q['choiceB']}
- C. {q['choiceC']}
- D. {q['choiceD']}

**正解:** {q['correct']}
""")

    # プロンプトを生成
    prompt = prompt_template.format(questions_list='\n'.join(questions_list))

    return prompt

def main():
    prompt = create_prompt_for_missing_questions()

    # ファイルに保存
    output_file = Path(r"C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\claude_chrome_prompt.md")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print("="*80)
    print("Claude for Chrome用プロンプトを作成しました")
    print("="*80)
    print(f"\n保存先: {output_file}")
    print(f"\nファイルサイズ: {output_file.stat().st_size:,} bytes")

    # プロンプトをコンソールにも表示
    print("\n\n" + "="*80)
    print("【生成されたプロンプト】")
    print("="*80)
    print(prompt)

if __name__ == "__main__":
    main()
