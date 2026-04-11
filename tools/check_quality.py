#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品質チェックスクリプト
全682問（実際は684問）の整合性を検証
"""
import csv
import re
import sys
from pathlib import Path
from datetime import datetime

# 標準出力のエンコーディング設定（Windows対応）
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class QualityChecker:
    def __init__(self, csv_path):
        self.csv_path = Path(csv_path)
        self.errors = []
        self.warnings = []
        self.stats = {
            'total': 0,
            'with_image': 0,
            'with_choice_image': 0,
            'five_choices': 0,
            'four_choices': 0,
            'multiple_correct': 0
        }

    def check_all(self):
        """全チェック実行"""
        print(f"品質チェック開始: {self.csv_path}")
        print("=" * 80)

        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):  # ヘッダー行は1行目
                self.stats['total'] += 1
                qid = row.get('qId', f'ROW{row_num}')

                # 各チェック実施
                self.check_choices(row, qid, row_num)
                self.check_correct_marker(row, qid, row_num)
                self.check_explanations(row, qid, row_num)
                self.check_image_urls(row, qid, row_num)
                self.check_required_fields(row, qid, row_num)

        # レポート生成
        self.generate_report()
        self.print_summary()

    def check_choices(self, row, qid, row_num):
        """選択肢の整合性チェック"""
        choices = {
            'A': row.get('choiceA', '').strip(),
            'B': row.get('choiceB', '').strip(),
            'C': row.get('choiceC', '').strip(),
            'D': row.get('choiceD', '').strip(),
            'E': row.get('choiceE', '').strip()
        }

        # A-Dは必須
        for letter in ['A', 'B', 'C', 'D']:
            if not choices[letter]:
                self.errors.append({
                    'qId': qid,
                    'row': row_num,
                    'severity': 'ERROR',
                    'category': '選択肢欠損',
                    'issue': f'選択肢{letter}が空です',
                    'recommendation': f'選択肢{letter}のテキストを設定してください'
                })

        # Eの有無で4択/5択を判定
        has_e = bool(choices['E'])
        if has_e:
            self.stats['five_choices'] += 1
        else:
            self.stats['four_choices'] += 1

        # 選択肢の長さチェック（極端に短い/長い）
        for letter, text in choices.items():
            if text:
                if len(text) < 5:
                    self.warnings.append({
                        'qId': qid,
                        'row': row_num,
                        'severity': 'WARNING',
                        'category': '選択肢長',
                        'issue': f'選択肢{letter}が極端に短い（{len(text)}文字）',
                        'recommendation': '意図通りか確認してください'
                    })
                elif len(text) > 500:
                    self.warnings.append({
                        'qId': qid,
                        'row': row_num,
                        'severity': 'WARNING',
                        'category': '選択肢長',
                        'issue': f'選択肢{letter}が極端に長い（{len(text)}文字）',
                        'recommendation': '表示崩れの可能性があります'
                    })

    def check_correct_marker(self, row, qid, row_num):
        """正解マーカーの検証"""
        correct = row.get('correct', '').strip().upper()
        choice_e = row.get('choiceE', '').strip()

        if not correct:
            self.errors.append({
                'qId': qid,
                'row': row_num,
                'severity': 'ERROR',
                'category': '正解マーカー欠損',
                'issue': 'correctフィールドが空です',
                'recommendation': '正解の選択肢を設定してください'
            })
            return

        # 複数選択の場合
        if ',' in correct:
            self.stats['multiple_correct'] += 1
            markers = [m.strip() for m in correct.split(',')]
            valid_markers = ['A', 'B', 'C', 'D']
            if choice_e:
                valid_markers.append('E')

            for marker in markers:
                if marker not in valid_markers:
                    self.errors.append({
                        'qId': qid,
                        'row': row_num,
                        'severity': 'ERROR',
                        'category': '正解マーカー不正',
                        'issue': f'不正な正解マーカー: {marker}（複数選択: {correct}）',
                        'recommendation': f'有効な選択肢（{",".join(valid_markers)}）を設定してください'
                    })
        else:
            # 単一選択
            valid_choices = ['A', 'B', 'C', 'D']
            if choice_e:
                valid_choices.append('E')

            if correct not in valid_choices:
                self.errors.append({
                    'qId': qid,
                    'row': row_num,
                    'severity': 'ERROR',
                    'category': '正解マーカー不正',
                    'issue': f'不正な正解マーカー: {correct}',
                    'recommendation': f'有効な選択肢（{",".join(valid_choices)}）を設定してください'
                })

            # Eを指しているが選択肢Eが存在しない
            if correct == 'E' and not choice_e:
                self.errors.append({
                    'qId': qid,
                    'row': row_num,
                    'severity': 'ERROR',
                    'category': '正解マーカー矛盾',
                    'issue': '正解がEだが選択肢Eが存在しません',
                    'recommendation': '選択肢Eを追加するか、正解を修正してください'
                })

    def check_explanations(self, row, qid, row_num):
        """説明文の妥当性チェック"""
        choice_e = row.get('choiceE', '').strip()

        explains = {
            'A': row.get('explainA', '').strip(),
            'B': row.get('explainB', '').strip(),
            'C': row.get('explainC', '').strip(),
            'D': row.get('explainD', '').strip(),
            'E': row.get('explainE', '').strip()
        }

        # 選択肢があるのに説明がない（警告レベル）
        choices = {
            'A': row.get('choiceA', '').strip(),
            'B': row.get('choiceB', '').strip(),
            'C': row.get('choiceC', '').strip(),
            'D': row.get('choiceD', '').strip(),
            'E': choice_e
        }

        for letter in ['A', 'B', 'C', 'D', 'E']:
            if choices[letter] and not explains[letter]:
                # 説明なしは警告（必須ではない運用の場合もある）
                self.warnings.append({
                    'qId': qid,
                    'row': row_num,
                    'severity': 'WARNING',
                    'category': '説明欠損',
                    'issue': f'選択肢{letter}に対する説明がありません',
                    'recommendation': f'explain{letter}の設定を推奨'
                })

        # 文字化けパターン検出（簡易）
        garbled_patterns = [
            r'[��]{2,}',  # 複数の置換文字
            r'[\x00-\x08\x0B\x0C\x0E-\x1F]',  # 制御文字
        ]

        for letter, text in explains.items():
            if text:
                for pattern in garbled_patterns:
                    if re.search(pattern, text):
                        self.errors.append({
                            'qId': qid,
                            'row': row_num,
                            'severity': 'ERROR',
                            'category': '文字化け疑い',
                            'issue': f'explain{letter}に文字化けの可能性があります',
                            'recommendation': '元データを確認してください'
                        })
                        break

    def check_image_urls(self, row, qid, row_num):
        """画像URLの有効性チェック"""
        image_url = row.get('imageUrl', '').strip()
        choice_image_url = row.get('choiceImageUrl', '').strip()

        # URL形式の簡易検証
        url_pattern = r'^https?://.+'

        if image_url:
            self.stats['with_image'] += 1
            if not re.match(url_pattern, image_url):
                self.errors.append({
                    'qId': qid,
                    'row': row_num,
                    'severity': 'ERROR',
                    'category': 'URL形式不正',
                    'issue': f'imageUrlの形式が不正です: {image_url[:50]}...',
                    'recommendation': 'http://またはhttps://で始まるURLを設定してください'
                })

        if choice_image_url:
            self.stats['with_choice_image'] += 1
            if not re.match(url_pattern, choice_image_url):
                self.errors.append({
                    'qId': qid,
                    'row': row_num,
                    'severity': 'ERROR',
                    'category': 'URL形式不正',
                    'issue': f'choiceImageUrlの形式が不正です: {choice_image_url[:50]}...',
                    'recommendation': 'http://またはhttps://で始まるURLを設定してください'
                })

    def check_required_fields(self, row, qid, row_num):
        """必須フィールドのチェック"""
        required_fields = {
            'qId': '問題ID',
            'segmentId': 'セグメントID',
            'type': '問題タイプ',
            'stem': '問題文'
        }

        for field, label in required_fields.items():
            if not row.get(field, '').strip():
                self.errors.append({
                    'qId': qid,
                    'row': row_num,
                    'severity': 'ERROR',
                    'category': '必須フィールド欠損',
                    'issue': f'{label}（{field}）が空です',
                    'recommendation': f'{label}を設定してください'
                })

        # stemの長さチェック
        stem = row.get('stem', '').strip()
        if stem and len(stem) < 10:
            self.warnings.append({
                'qId': qid,
                'row': row_num,
                'severity': 'WARNING',
                'category': '問題文が短い',
                'issue': f'問題文が極端に短い（{len(stem)}文字）',
                'recommendation': '意図通りか確認してください'
            })

    def generate_report(self):
        """CSVレポート生成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.csv_path.parent / f'quality_check_report_{timestamp}.csv'

        # エラーと警告を結合してソート
        all_issues = self.errors + self.warnings
        all_issues.sort(key=lambda x: (x['row'], x['severity']))

        if not all_issues:
            print(f"\n✓ 問題は検出されませんでした")
            return

        with open(report_path, 'w', encoding='utf-8-sig', newline='') as f:
            fieldnames = ['qId', 'row', 'severity', 'category', 'issue', 'recommendation']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_issues)

        print(f"\nレポート生成: {report_path}")
        print(f"  - エラー: {len(self.errors)}件")
        print(f"  - 警告: {len(self.warnings)}件")

    def print_summary(self):
        """サマリー表示"""
        print("\n" + "=" * 80)
        print("品質チェック結果サマリー")
        print("=" * 80)
        print(f"総問題数: {self.stats['total']}")
        print(f"4択問題: {self.stats['four_choices']}")
        print(f"5択問題: {self.stats['five_choices']}")
        print(f"複数選択: {self.stats['multiple_correct']}")
        print(f"画像付き問題: {self.stats['with_image']}")
        print(f"選択肢画像付き: {self.stats['with_choice_image']}")
        print()
        print(f"エラー: {len(self.errors)}件")
        print(f"警告: {len(self.warnings)}件")

        # エラーの内訳
        if self.errors:
            print("\n【エラー内訳】")
            error_categories = {}
            for err in self.errors:
                cat = err['category']
                error_categories[cat] = error_categories.get(cat, 0) + 1
            for cat, count in sorted(error_categories.items(), key=lambda x: -x[1]):
                print(f"  - {cat}: {count}件")

        # 警告の内訳
        if self.warnings:
            print("\n【警告内訳】")
            warning_categories = {}
            for warn in self.warnings:
                cat = warn['category']
                warning_categories[cat] = warning_categories.get(cat, 0) + 1
            for cat, count in sorted(warning_categories.items(), key=lambda x: -x[1]):
                print(f"  - {cat}: {count}件")

        # 代表的なエラー例（最大5件）
        if self.errors:
            print("\n【代表的なエラー（最大5件）】")
            for i, err in enumerate(self.errors[:5], 1):
                print(f"{i}. [{err['qId']}] {err['issue']}")
                print(f"   推奨: {err['recommendation']}")

def main():
    csv_path = Path(__file__).parent / 'questionbank_drive_import.csv'

    if not csv_path.exists():
        print(f"エラー: ファイルが見つかりません: {csv_path}")
        sys.exit(1)

    checker = QualityChecker(csv_path)
    checker.check_all()

    # エラーがある場合は終了コード1
    if checker.errors:
        sys.exit(1)

if __name__ == '__main__':
    main()
