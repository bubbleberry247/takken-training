# -*- coding: utf-8 -*-
"""
CSVの統合解説(explainShort)を選択肢別に自動分解するスクリプト

対象: R2/R3年度の問題でexplainA-Dが空白だがexplainShortに統合解説があるもの
"""
import csv
import re
import sys
import io
from typing import Dict, List, Optional, Tuple

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class ExplanationSplitter:
    """統合解説を選択肢別に分解するクラス"""

    # パターン1: "1→判定。理由..." （半角数字 + 矢印）
    PATTERN_ARROW_HALFWIDTH = re.compile(
        r'(?:^|\s+)([1234])→(.+?)(?=\s*[1234]→|$)',
        re.DOTALL
    )

    # パターン1-2: "1.判定。理由..." （半角数字 + ピリオド）
    PATTERN_DOT_HALFWIDTH = re.compile(
        r'(?:^|\s+)([1234])\.(.+?)(?=\s*[1234]\.|$)',
        re.DOTALL
    )

    # パターン2: "選択肢1. 文..."
    PATTERN_CHOICE_PREFIX = re.compile(
        r'選択肢([１234])\.\s*(.+?)(?=選択肢[１234]\.|$)',
        re.DOTALL
    )

    # パターン3: R3年度形式 "１．判定。理由..." （全角数字 + 全角ピリオド）
    PATTERN_FULLWIDTH = re.compile(
        r'(?:^|\s+)([○×✖〇]?)([１234])[\.\．](.+?)(?=\s*[○×✖〇]?[１234][\.\．]|$)',
        re.DOTALL
    )

    # 判定ワード（正解/不正解の判定が含まれているか確認用）
    JUDGEMENT_WORDS = [
        '正しい', '誤り', '適当', '不適当',
        '正解', '不正解', '設問通り', '問題文の通り'
    ]

    def normalize_number(self, num_str: str) -> int:
        """全角・半角数字を正規化"""
        fullwidth_map = {'１': 1, '２': 2, '３': 3, '４': 4}
        if num_str in fullwidth_map:
            return fullwidth_map[num_str]
        try:
            return int(num_str)
        except:
            return 0

    def split_by_regex(self, text: str) -> Optional[Dict[str, str]]:
        """正規表現で選択肢別に分解"""

        # パターン1: 半角数字 "1→"
        matches = self.PATTERN_ARROW_HALFWIDTH.findall(text)
        if matches and len(matches) >= 3:  # 最低3つあればOK
            result = {}
            for num, explanation in matches:
                num_int = self.normalize_number(num)
                if num_int > 0 and num_int <= 4:
                    choice = ['A', 'B', 'C', 'D'][num_int - 1]
                    result[choice] = explanation.strip()

            if len(result) >= 3 and self._validate_explanations(result):
                return result

        # パターン1-2: 半角数字 "1."
        matches = self.PATTERN_DOT_HALFWIDTH.findall(text)
        if matches and len(matches) >= 3:
            result = {}
            for num, explanation in matches:
                num_int = self.normalize_number(num)
                if num_int > 0 and num_int <= 4:
                    choice = ['A', 'B', 'C', 'D'][num_int - 1]
                    result[choice] = explanation.strip()

            if len(result) >= 3 and self._validate_explanations(result):
                return result

        # パターン2: R3年度形式 "○１．" または "✖４．"
        matches = self.PATTERN_FULLWIDTH.findall(text)
        if matches and len(matches) >= 3:
            result = {}
            for mark, num, explanation in matches:
                num_int = self.normalize_number(num)
                if num_int > 0 and num_int <= 4:
                    choice = ['A', 'B', 'C', 'D'][num_int - 1]
                    # マーク（○✖）も説明に含める
                    full_explanation = (mark + explanation).strip() if mark else explanation.strip()
                    result[choice] = full_explanation

            if len(result) >= 3 and self._validate_explanations(result):
                return result

        # パターン3: "選択肢1."
        matches = self.PATTERN_CHOICE_PREFIX.findall(text)
        if matches and len(matches) >= 3:
            result = {}
            for num, explanation in matches:
                num_int = self.normalize_number(num)
                if num_int > 0 and num_int <= 4:
                    choice = ['A', 'B', 'C', 'D'][num_int - 1]
                    result[choice] = explanation.strip()

            if len(result) >= 3 and self._validate_explanations(result):
                return result

        return None

    def _validate_explanations(self, explanations: Dict[str, str]) -> bool:
        """選択肢説明の妥当性を検証"""
        if len(explanations) < 3:
            return False

        # 少なくとも2つの選択肢に判定ワードが含まれているか
        count = 0
        for exp in explanations.values():
            if any(word in exp for word in self.JUDGEMENT_WORDS):
                count += 1

        return count >= 2

    def extract_from_integrated(
        self,
        integrated_explanation: str
    ) -> Tuple[Optional[Dict[str, str]], str]:
        """
        統合解説から選択肢別説明を抽出

        Returns:
            (選択肢別説明, 抽出方法)
        """
        result = self.split_by_regex(integrated_explanation)
        if result:
            if '→' in integrated_explanation:
                return (result, 'regex_arrow')
            elif any(c in integrated_explanation for c in ['○', '×', '✖', '〇']):
                return (result, 'regex_fullwidth_marked')
            else:
                return (result, 'regex_fullwidth')

        return (None, 'failed')


def process_csv(input_file: str, output_file: str):
    """CSVファイルを処理"""

    splitter = ExplanationSplitter()

    # 統計
    stats = {
        'total': 0,
        'already_has_explanations': 0,
        'no_integrated': 0,
        'regex_arrow': 0,
        'regex_fullwidth': 0,
        'regex_fullwidth_marked': 0,
        'failed': 0
    }

    updated_rows = []
    failed_cases = []

    # CSVを読み込み
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # 処理
    for row in rows:
        stats['total'] += 1
        qId = row['qId']

        # R2/R3年度のみ処理
        if not (qId.startswith('R2') or qId.startswith('R3')):
            continue

        # 既に選択肢説明がある場合はスキップ
        if row.get('explainA') and row.get('explainB') and row.get('explainC') and row.get('explainD'):
            stats['already_has_explanations'] += 1
            continue

        # 統合解説を取得
        integrated = row.get('explainShort', '') or row.get('explainLong', '')
        if not integrated:
            stats['no_integrated'] += 1
            continue

        # 分解を試みる
        result, method = splitter.extract_from_integrated(integrated)

        if result:
            # 成功
            row['explainA'] = result.get('A', '')
            row['explainB'] = result.get('B', '')
            row['explainC'] = result.get('C', '')
            row['explainD'] = result.get('D', '')

            stats[method] += 1
            updated_rows.append({
                'qId': qId,
                'method': method,
                'explainA': result.get('A', '')[:50],
                'explainB': result.get('B', '')[:50],
                'explainC': result.get('C', '')[:50],
                'explainD': result.get('D', '')[:50]
            })

            print(f"✓ {qId}: 分解成功 ({method})")
        else:
            # 失敗
            stats['failed'] += 1
            failed_cases.append({
                'qId': qId,
                'integrated': integrated[:300]
            })

            print(f"✗ {qId}: 分解失敗")

    # CSVを保存
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # 失敗ケースを保存
    if failed_cases:
        with open('split_failed_cases_csv.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(failed_cases, f, ensure_ascii=False, indent=2)

    # 統計レポート
    print("\n" + "=" * 80)
    print("処理結果")
    print("=" * 80)
    print(f"総問題数: {stats['total']}")
    print(f"既に選択肢説明あり: {stats['already_has_explanations']}")
    print(f"統合解説なし: {stats['no_integrated']}")
    print(f"今回分解成功:")
    print(f"  - 矢印形式 (N→): {stats['regex_arrow']}")
    print(f"  - 全角数字形式 (Ｎ．): {stats['regex_fullwidth']}")
    print(f"  - マーク付き全角形式 (○Ｎ．): {stats['regex_fullwidth_marked']}")
    total_success = stats['regex_arrow'] + stats['regex_fullwidth'] + stats['regex_fullwidth_marked']
    print(f"  - 合計: {total_success}")
    print(f"分解失敗（LLM処理候補）: {stats['failed']}")
    print()

    processable = stats['total'] - stats['already_has_explanations'] - stats['no_integrated']
    if processable > 0:
        success_rate = (total_success / processable) * 100
        print(f"分解成功率: {success_rate:.1f}%")
    print()
    print(f"更新後のデータ: {output_file}")
    if failed_cases:
        print(f"分解失敗ケース: split_failed_cases_csv.json ({len(failed_cases)}件)")

    # サンプル表示
    if updated_rows:
        print("\n" + "=" * 80)
        print("分解成功サンプル（最初の5件）")
        print("=" * 80)
        for i, row in enumerate(updated_rows[:5], 1):
            print(f"\n【{i}】 {row['qId']} ({row['method']})")
            print(f"explainA: {row['explainA']}...")
            print(f"explainB: {row['explainB']}...")
            print(f"explainC: {row['explainC']}...")
            print(f"explainD: {row['explainD']}...")


def main():
    input_file = 'questionbank_drive_import.csv'
    output_file = 'questionbank_drive_import_split.csv'

    print("CSV統合解説の自動分解スクリプト")
    print("=" * 80)
    print(f"入力: {input_file}")
    print(f"出力: {output_file}")
    print()

    process_csv(input_file, output_file)


if __name__ == '__main__':
    main()
