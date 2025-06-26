# utils.py
import textwrap
import json
import random
from pathlib import Path
from typing import Optional, Union, Any

def wrap_text(text, width=70):
    """Helper function to wrap text for better readability."""
    return "\n".join(textwrap.wrap(str(text), width))

def generate_text_bar_chart(data, label_key, value_key, max_width=50, char='█'):
    """Generates a text-based bar chart."""
    if not data:
        return "No data to generate chart."

    # Sort data for better visualization, e.g., by score ascending
    sorted_data = sorted(data, key=lambda x: x.get(value_key, 0))

    max_label_len = max(len(str(item[label_key])) for item in sorted_data)
    chart_lines = []

    for item in sorted_data:
        label = str(item[label_key]).ljust(max_label_len)
        value = item.get(value_key, 0)
        if not isinstance(value, (int, float)):
            value = 0
        
        num_blocks = int((value / 100) * max_width)
        bar = char * num_blocks
        empty_space = ' ' * (max_width - num_blocks)
        
        chart_lines.append(f"{label}: [{bar}{empty_space}] {value}%")
    
    return "\n".join(chart_lines)

def stratified_sample_questions(questions_by_skill: dict, total_requested: int) -> list:
    """
    Perform stratified sampling to ensure representation across skill areas.
    
    Args:
        questions_by_skill: Dict mapping skill areas to lists of questions
        total_requested: Total number of questions requested
        
    Returns:
        List of sampled questions
    """
    if not questions_by_skill:
        return []
        
    skill_areas = list(questions_by_skill.keys())
    total_available = sum(len(questions) for questions in questions_by_skill.values())
    
    if total_requested >= total_available:
        all_questions = []
        for questions in questions_by_skill.values():
            all_questions.extend(questions)
        return all_questions
    
    selected_questions = []
    base_per_skill = max(1, total_requested // len(skill_areas))
    remaining = total_requested - (base_per_skill * len(skill_areas))
    
    # First pass: allocate base amount to each skill area
    for skill_area in skill_areas:
        available_in_skill = len(questions_by_skill[skill_area])
        to_sample = min(base_per_skill, available_in_skill)
        
        if to_sample > 0:
            sampled = random.sample(questions_by_skill[skill_area], to_sample)
            selected_questions.extend(sampled)
            
            for q in sampled:
                questions_by_skill[skill_area].remove(q)
    
    # Second pass: distribute remaining questions
    while remaining > 0 and any(len(questions) > 0 for questions in questions_by_skill.values()):
        for skill_area in skill_areas:
            if remaining <= 0:
                break
                
            if len(questions_by_skill[skill_area]) > 0:
                sampled = random.sample(questions_by_skill[skill_area], 1)
                selected_questions.extend(sampled)
                questions_by_skill[skill_area].remove(sampled[0])
                remaining -= 1
    
    return selected_questions

def parse_score(score_value: Union[str, int, float, None]) -> float:
    """
    Parse score value, handling various input formats robustly.
    
    Args:
        score_value: Score in various formats (string percentage, numeric, None)
        
    Returns:
        float: Parsed score as a number (0-100 range)
    """
    if score_value is None:
        return 0.0
    
    try:
        if isinstance(score_value, (int, float)):
            return float(score_value)
        
        if isinstance(score_value, str):
            # Handle percentage strings
            cleaned = score_value.strip().replace('%', '')
            if cleaned:
                return float(cleaned)
            return 0.0
    except (ValueError, TypeError):
        print(f"Error parsing score value: {score_value}. Returning 0.0.")
        pass
    
    return 0.0  # Default to 0.0 if parsing fails

def construct_file_path(files_dir: Path, exam_code: str, suffix: str) -> Path:
    """Construct standardized file paths."""
    return files_dir / f"{exam_code}_{suffix}"

def load_json_file(file_path: Path) -> Optional[Any]:
    """Load JSON file with error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{file_path}'. File might be corrupted.")
        return None

def save_json_file(data: Any, file_path: Path) -> bool:
    """Save data to JSON file with error handling."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving to '{file_path}': {e}")
        return False
