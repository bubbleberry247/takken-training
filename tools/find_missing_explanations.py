# -*- coding: utf-8 -*-
"""
R2/R3年度の説明文欠落問題を特定し、原本からサンプル抽出
"""
import json
import sys
import io

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# all_questions.jsonを読み込み
with open('all_questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# R2, R3年度で説明文が欠落している問題を特定
r2_missing = []
r3_missing = []

def has_all_explanations(q):
    """全ての選択肢説明があるかチェック"""
    return bool(
        q.get('explainA') and
        q.get('explainB') and
        q.get('explainC') and
        q.get('explainD')
    )

# 各年度のデータを走査
for year_key, questions in data.items():
    if not isinstance(questions, list):
        continue

    # 年度を抽出
    if 'R2' in year_key:
        year = 'R2'
    elif 'R3' in year_key:
        year = 'R3'
    else:
        continue

    for q in questions:
        if not isinstance(q, dict):
            continue

        qNum = q.get('qNum', '')
        has_explain = has_all_explanations(q)

        # ID生成（既存ロジックと同じ）
        category = year_key.split('gakka')[1] if 'gakka' in year_key else ''
        q_id = f"{year}_{category}_{qNum:02d}" if isinstance(qNum, int) else f"{year}_{category}_{qNum}"

        missing_info = {
            'qId': q_id,
            'yearKey': year_key,
            'qNum': qNum,
            'stem': q.get('stem', '')[:100],
            'explainShort': q.get('explainShort', ''),
            'explainLong': q.get('explainLong', ''),
            'has_explainShort': bool(q.get('explainShort')),
            'has_explainLong': bool(q.get('explainLong'))
        }

        if year == 'R2' and not has_explain:
            r2_missing.append(missing_info)
        elif year == 'R3' and not has_explain:
            r3_missing.append(missing_info)

print(f"R2年度 欠落問題数: {len(r2_missing)}/96")
print(f"R3年度 欠落問題数: {len(r3_missing)}/96")
print()

print("=" * 80)
print("=== R2年度サンプル（最初の10問）===")
print("=" * 80)
for i, q in enumerate(r2_missing[:10], 1):
    print(f"\n【{i}】 qId: {q['qId']} (年度キー: {q['yearKey']})")
    print(f"問題文: {q['stem']}...")
    print(f"統合解説あり: explainShort={q['has_explainShort']}, explainLong={q['has_explainLong']}")
    if q['explainShort']:
        print(f"explainShort内容: {q['explainShort'][:200]}...")
    if q['explainLong']:
        print(f"explainLong内容: {q['explainLong'][:200]}...")

print("\n" + "=" * 80)
print("=== R3年度サンプル（最初の10問）===")
print("=" * 80)
for i, q in enumerate(r3_missing[:10], 1):
    print(f"\n【{i}】 qId: {q['qId']} (年度キー: {q['yearKey']})")
    print(f"問題文: {q['stem']}...")
    print(f"統合解説あり: explainShort={q['has_explainShort']}, explainLong={q['has_explainLong']}")
    if q['explainShort']:
        print(f"explainShort内容: {q['explainShort'][:200]}...")
    if q['explainLong']:
        print(f"explainLong内容: {q['explainLong'][:200]}...")

# サンプルをJSONで保存
with open('missing_explanations_samples.json', 'w', encoding='utf-8') as f:
    json.dump({
        'R2': r2_missing[:20],
        'R3': r3_missing[:20]
    }, f, ensure_ascii=False, indent=2)

print("\n\nサンプルデータを missing_explanations_samples.json に保存しました")
