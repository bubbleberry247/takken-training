#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Word文書の生データサンプリング
実際の段落内容を確認して、形式の違いを特定
"""

import sys
import io
from pathlib import Path
from docx import Document

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ORIGINAL_FOLDER = Path(r"C:\Users\masam\Downloads\１級土木-20260214T233348Z-1-001\１級土木")

def sample_word_paragraphs(file_path, start=0, count=30):
    """Word文書の段落を生出力"""
    try:
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs]

        return paragraphs[start:start+count]
    except Exception as e:
        return [f"ERROR: {e}"]

def main():
    print("=" * 80)
    print("Word原本ファイル 生データサンプリング")
    print("=" * 80)

    # 調査対象：令和7年度 vs 令和1年度（形式比較）
    target_files = [
        ("令和7年度 (最新・最大)", "1級土木 解説文集 令和7年度.docx", 0, 50),
        ("令和1年度 (抽出率0%)", "1級土木 解説文集 令和元年度.docx", 0, 50),
        ("令和5年度 (抽出率高)", "1級土木 解説文集 令和5年度.docx", 0, 50),
    ]

    for label, filename, start, count in target_files:
        file_path = ORIGINAL_FOLDER / filename

        if not file_path.exists():
            print(f"\n## {label}")
            print(f"❌ ファイルが存在しません")
            continue

        print(f"\n## {label}")
        print(f"ファイル: {filename}")
        print(f"サンプル範囲: 段落 {start+1}～{start+count}")
        print("\n" + "-" * 80)

        paragraphs = sample_word_paragraphs(file_path, start, count)

        for i, para in enumerate(paragraphs, start=start+1):
            # 空行を表示
            if not para.strip():
                print(f"{i:3d}. [空行]")
            else:
                # 長い段落は省略
                display = para if len(para) <= 100 else para[:100] + "..."
                print(f"{i:3d}. {display}")

        print("\n" + "=" * 80)

    print("\n## 形式比較分析")
    print("\n### 令和7年度の特徴")
    print("- 問題番号形式: 「問1（問題A ユニットa 問1）」")
    print("- 明確なセクション: 【問題文】【選択肢】【解説】")
    print("- 選択肢形式: 「1. ρt＝m／V...」")
    print("")
    print("### 令和1年度の特徴")
    print("- 問題番号形式: 「問1（ID: 47839）」")
    print("- 区切り線: 「────」を使用")
    print("- 選択肢説明: explainA/B/C/D形式ではない可能性")
    print("")
    print("### 推測")
    print("1. **令和7年度は新形式** → 抽出スクリプトが未対応")
    print("2. **令和1-3年度は旧形式** → 区切り線ベースの構造")
    print("3. **令和5年度は移行期** → 抽出率が高い = 現在のスクリプトに適合")

if __name__ == '__main__':
    main()
