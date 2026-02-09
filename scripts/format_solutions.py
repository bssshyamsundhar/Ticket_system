"""
Script to convert bot_solution in data.json to numbered format
This will split sentences and format them as numbered steps
"""
import json
import re
import os

def format_solution_as_numbered(solution):
    """Convert a solution paragraph into numbered steps"""
    # Split by periods, but not by periods in abbreviations
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', solution.strip())
    
    if len(sentences) <= 1:
        return solution  # Keep as is if only one sentence
    
    # Format as numbered list
    numbered_steps = []
    for i, sentence in enumerate(sentences, 1):
        sentence = sentence.strip()
        if sentence and not sentence.endswith('.'):
            sentence += '.'
        if sentence:
            numbered_steps.append(f"{i}. {sentence}")
    
    return "\n".join(numbered_steps)

def process_data(data):
    """Recursively process the data and format solutions"""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "bot_solution" and isinstance(value, str):
                data[key] = format_solution_as_numbered(value)
            else:
                process_data(value)
    elif isinstance(data, list):
        for item in data:
            process_data(item)

def main():
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'kb', 'data', 'data.json')
    
    print(f"Reading {data_path}...")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("Converting solutions to numbered format...")
    process_data(data)
    
    # Backup original
    backup_path = data_path + '.backup'
    print(f"Creating backup at {backup_path}...")
    
    # Write updated data
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("✅ Done! Solutions are now in numbered format.")

if __name__ == '__main__':
    main()
