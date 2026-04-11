"""
Integrate manually entered answers for R4 and R6 into the parsed question JSON.
"""
import json
from pathlib import Path

# Manual answer data
R4_ANSWERS = {
    'A': [3,1,3,4,1,2,1,4,3,1,4,1,3,2,1,1,3,4,2,2,4,3,  # 1-22
          2,2,1,3,3,1,2,2,4,2,2,4,4,1,2,1,3,1,4,2,4,3,  # 23-44
          3,2,4,4,3,2,1,2,3,4,3,3,4,4,2,3,1],            # 45-61
    'B': [3,1,3,4,2,1,1,4,1,2,1,2,3,3,4,3,4,2,1,1,2,3,  # 1-22
          2,4,3,4,2,4,2,4,1,3,4,3,1]                     # 23-35 (公式PDF R4gakka_kaitou.pdf準拠)
}

R5_ANSWERS = {
    'A': [2,4,4,1,4,1,4,3,4,2,3,2,4,1,1,2,1,3,1,1,3,4,  # 1-22
          3,1,4,4,2,4,3,2,3,1,2,4,2,4,2,2,1,3,4,2,4,3,  # 23-44
          4,3,2,2,3,1,3,2,3,2,1,1,2,4,1,3,3],            # 45-61
    'B': [1,3,1,2,3,2,4,4,2,4,3,4,2,4,1,4,1,1,3,2,1,3,  # 1-22
          2,3,4,1,4,3,4,2,2,2,3,3,2]                     # 23-35
}

R6_ANSWERS = {
    'A': [4,2,2,4,1,2,3,4,1,4,4,2,1,4,3,1,4,2,4,3,2,2,  # 1-22
          1,4,3,2,4,1,3,1,2,1,3,2,3,1,4,1,1,2,3,4,3,1,  # 23-44
          2,1,3,1,2,4,4,1,2,2,4,2,3,1,3,4,3,3,2,1,3,3],  # 45-66
    'B': [2,2,3,1,2,2,1,1,4,1,3,4,4,3,3,1,3,4,2,1,4,2,  # 1-22
          1,3,2,1,4,3,4,3,3,4,4,1,3]                     # 23-35
}

def integrate_answers(input_json: Path, output_json: Path):
    """Add manual answers to R4 and R6 questions."""
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Add R4 answers
    for section in ['A', 'B']:
        key = f'R4gakka{section}'
        if key in data:
            answers = R4_ANSWERS[section]
            print(f'{key}: Adding {len(answers)} answers to {len(data[key])} questions')
            for i, q in enumerate(data[key]):
                if i < len(answers):
                    q['correct'] = answers[i]
                else:
                    print(f'  Warning: Question {i+1} has no answer (total {len(answers)} answers)')

    # Add R5 answers
    for section in ['A', 'B']:
        key = f'R5gakka{section}'
        if key in data:
            answers = R5_ANSWERS[section]
            print(f'{key}: Adding {len(answers)} answers to {len(data[key])} questions')
            for i, q in enumerate(data[key]):
                if i < len(answers):
                    q['correct'] = answers[i]
                else:
                    print(f'  Warning: Question {i+1} has no answer (total {len(answers)} answers)')

    # Add R6 answers
    for section in ['A', 'B']:
        key = f'R6gakka{section}'
        if key in data:
            answers = R6_ANSWERS[section]
            print(f'{key}: Adding {len(answers)} answers to {len(data[key])} questions')
            for i, q in enumerate(data[key]):
                if i < len(answers):
                    q['correct'] = answers[i]
                else:
                    print(f'  Warning: Question {i+1} has no answer (total {len(answers)} answers)')

    # Save updated data
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Stats
    total_questions = sum(len(qs) for qs in data.values())
    with_answers = sum(1 for qs in data.values() for q in qs if 'correct' in q)
    print(f'\nTotal questions: {total_questions}')
    print(f'With answers: {with_answers}')
    print(f'Saved to {output_json}')

if __name__ == '__main__':
    input_path = Path('questions_parsed.json')
    output_path = Path('questions_parsed_complete.json')
    integrate_answers(input_path, output_path)
