# -*- coding: utf-8 -*-
"""
統合解説形式を選択肢別に自動分解するスクリプト

戦略: ハイブリッドアプローチ
1. 正規表現で分解（パターンA: 選択肢区切りが明確）
2. 失敗時はLLMに委託（パターンB: 統合解説のみ）
"""
import json
import re
import sys
import io
from typing import Dict, List, Optional, Tuple

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class ExplanationSplitter:
    """統合解説を選択肢別に分解するクラス"""

    # パターンA: "1→判定。理由..." または "1.判定。理由..."
    PATTERN_ARROW = re.compile(
        r'(?:^|\s+)(\d+)[\.\→](.+?)(?=\s*\d+[\.\→]|$)',
        re.DOTALL
    )

    # パターンA変形: "選択肢1. 文..."
    PATTERN_CHOICE_PREFIX = re.compile(
        r'選択肢(\d+)\.\s*(.+?)(?=選択肢\d+\.|$)',
        re.DOTALL
    )

    # 判定ワード（正解/不正解の判定が含まれているか確認用）
    JUDGEMENT_WORDS = [
        '正しい', '誤り', '適当', '不適当',
        '正解', '不正解', '設問通り'
    ]

    def split_by_regex(self, text: str) -> Optional[Dict[str, str]]:
        """正規表現で選択肢別に分解"""
        # パターン1: "1→" または "1."
        matches = self.PATTERN_ARROW.findall(text)
        if matches and len(matches) == 4:
            result = {}
            for num, explanation in matches:
                choice = ['A', 'B', 'C', 'D'][int(num) - 1]
                result[choice] = explanation.strip()

            # 検証: 全ての選択肢に判定ワードが含まれているか
            if self._validate_explanations(result):
                return result

        # パターン2: "選択肢1."
        matches = self.PATTERN_CHOICE_PREFIX.findall(text)
        if matches and len(matches) == 4:
            result = {}
            for num, explanation in matches:
                choice = ['A', 'B', 'C', 'D'][int(num) - 1]
                result[choice] = explanation.strip()

            if self._validate_explanations(result):
                return result

        return None

    def _validate_explanations(self, explanations: Dict[str, str]) -> bool:
        """選択肢説明の妥当性を検証"""
        # 少なくとも2つの選択肢に判定ワードが含まれているか
        count = 0
        for exp in explanations.values():
            if any(word in exp for word in self.JUDGEMENT_WORDS):
                count += 1

        return count >= 2

    def extract_from_integrated(
        self,
        question_text: str,
        choices: Dict[str, str],
        integrated_explanation: str
    ) -> Tuple[Optional[Dict[str, str]], str]:
        """
        統合解説から選択肢別説明を抽出

        Returns:
            (選択肢別説明, 抽出方法)
            選択肢別説明: {'A': '...', 'B': '...', 'C': '...', 'D': '...'}
            抽出方法: 'regex_arrow', 'regex_choice_prefix', 'failed'
        """
        # 正規表現で試行
        result = self.split_by_regex(integrated_explanation)
        if result:
            if '→' in integrated_explanation:
                return (result, 'regex_arrow')
            else:
                return (result, 'regex_choice_prefix')

        return (None, 'failed')


def process_all_questions(input_file: str, output_file: str):
    """全問題を処理"""

    # データ読み込み
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    splitter = ExplanationSplitter()

    # 統計
    stats = {
        'total': 0,
        'already_has_explanations': 0,
        'regex_arrow': 0,
        'regex_choice_prefix': 0,
        'failed': 0
    }

    updated_questions = []
    failed_questions = []

    # 各年度のデータを走査
    for year_key, questions in data.items():
        if not isinstance(questions, list):
            continue

        print(f"\n処理中: {year_key}")

        for q in questions:
            if not isinstance(q, dict):
                continue

            stats['total'] += 1
            qNum = q.get('qNum', '')

            # 既に選択肢説明がある場合はスキップ
            if q.get('explainA') and q.get('explainB') and q.get('explainC') and q.get('explainD'):
                stats['already_has_explanations'] += 1
                continue

            # 統合解説を取得
            integrated = q.get('explainShort', '') or q.get('explainLong', '')
            if not integrated:
                # 統合解説もない
                continue

            # 選択肢を取得
            choices = q.get('choices', {})
            if not choices or len(choices) != 4:
                continue

            # 分解を試みる
            result, method = splitter.extract_from_integrated(
                q.get('stem', ''),
                choices,
                integrated
            )

            if result:
                # 成功
                q['explainA'] = result['A']
                q['explainB'] = result['B']
                q['explainC'] = result['C']
                q['explainD'] = result['D']

                stats[method] += 1
                updated_questions.append({
                    'year_key': year_key,
                    'qNum': qNum,
                    'method': method
                })

                print(f"  問{qNum}: 分解成功 ({method})")
            else:
                # 失敗
                stats['failed'] += 1
                failed_questions.append({
                    'year_key': year_key,
                    'qNum': qNum,
                    'integrated': integrated[:200]
                })

                print(f"  問{qNum}: 分解失敗")

    # 結果を保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 失敗ケースを保存（LLM処理用）
    with open('split_failed_cases.json', 'w', encoding='utf-8') as f:
        json.dump(failed_questions, f, ensure_ascii=False, indent=2)

    # 統計レポート
    print("\n" + "=" * 80)
    print("処理結果")
    print("=" * 80)
    print(f"総問題数: {stats['total']}")
    print(f"既に選択肢説明あり: {stats['already_has_explanations']}")
    print(f"今回分解成功:")
    print(f"  - 矢印形式 (N→): {stats['regex_arrow']}")
    print(f"  - 選択肢形式 (選択肢N.): {stats['regex_choice_prefix']}")
    print(f"  - 合計: {stats['regex_arrow'] + stats['regex_choice_prefix']}")
    print(f"分解失敗（LLM処理候補）: {stats['failed']}")
    print()

    success_rate = (stats['regex_arrow'] + stats['regex_choice_prefix']) / (stats['total'] - stats['already_has_explanations']) * 100 if stats['total'] > stats['already_has_explanations'] else 0
    print(f"分解成功率: {success_rate:.1f}%")
    print()
    print(f"更新後のデータ: {output_file}")
    print(f"分解失敗ケース: split_failed_cases.json")

    # サンプル表示
    if updated_questions:
        print("\n" + "=" * 80)
        print("分解成功サンプル（最初の3件）")
        print("=" * 80)
        for i, uq in enumerate(updated_questions[:3], 1):
            year_key = uq['year_key']
            qNum = uq['qNum']

            # 該当問題を探す
            for questions in data.values():
                if isinstance(questions, list):
                    for q in questions:
                        if q.get('qNum') == qNum:
                            print(f"\n【{i}】 {year_key} 問{qNum} ({uq['method']})")
                            print(f"explainA: {q['explainA'][:100]}...")
                            print(f"explainB: {q['explainB'][:100]}...")
                            print(f"explainC: {q['explainC'][:100]}...")
                            print(f"explainD: {q['explainD'][:100]}...")
                            break


def main():
    input_file = 'all_questions.json'
    output_file = 'all_questions_split.json'

    print("統合解説の自動分解スクリプト")
    print("=" * 80)
    print(f"入力: {input_file}")
    print(f"出力: {output_file}")
    print()

    process_all_questions(input_file, output_file)


if __name__ == '__main__':
    main()
