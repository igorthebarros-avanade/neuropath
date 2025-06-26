# utils.py
import os
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

def validate_unique_question_ids(auto_delete_duplicates: bool = False) -> None:
    """
    Validate that all question_ids in content_updated.json are unique using set() validation.
    
    Args:
        auto_delete_duplicates: If True, automatically removes duplicate question_ids
    
    Raises:
        AssertionError: If duplicate question_ids are found and auto_delete_duplicates is False
        FileNotFoundError: If content file doesn't exist
        json.JSONDecodeError: If content file is malformed
    """
    # Get content file path
    content_file = Path(os.getenv("EXAM_DATA_JSON_PATH"))
    
    print(f"🔍 Reading file: {content_file}")
    
    # Load content data
    with open(content_file, 'r', encoding='utf-8') as f:
        content_data = json.load(f)
    
    print(f"📁 Found {len(content_data)} exams in content file")
    
    # Extract all question_ids and track their locations
    all_question_ids = []
    question_locations = []  # Track where each question_id appears
    
    for exam_code, exam_data in content_data.items():
        print(f"Processing exam: {exam_code}")
            
        skills = exam_data.get("skills_measured", [])
        
        for skill_idx, skill in enumerate(skills):
            skill_area = skill.get("skill_area", "")
            subtopics = skill.get("subtopics", [])
            
            for subtopic_idx, subtopic in enumerate(subtopics):
                if isinstance(subtopic, dict):
                    details = subtopic.get("details", [])
                    
                    for detail_idx, detail in enumerate(details):
                        # Process main question
                        if isinstance(detail, dict) and detail.get("question_id"):
                            question_id = detail["question_id"]
                            all_question_ids.append(question_id)
                            question_locations.append({
                                "exam": exam_code,
                                "skill_idx": skill_idx,
                                "subtopic_idx": subtopic_idx,
                                "detail_idx": detail_idx,
                                "is_alternative": False,
                                "alt_idx": None
                            })
                        
                        # Process alternative questions
                        if isinstance(detail, dict) and isinstance(detail.get('alternative_questions'), list):
                            for alt_idx, alt_question in enumerate(detail['alternative_questions']):
                                if isinstance(alt_question, dict) and alt_question.get("question_id"):
                                    question_id = alt_question["question_id"]
                                    all_question_ids.append(question_id)
                                    question_locations.append({
                                        "exam": exam_code,
                                        "skill_idx": skill_idx,
                                        "subtopic_idx": subtopic_idx,
                                        "detail_idx": detail_idx,
                                        "is_alternative": True,
                                        "alt_idx": alt_idx
                                    })

    # Find duplicates for detailed reporting
    from collections import Counter
    id_counts = Counter(all_question_ids)
    duplicates = {qid: count for qid, count in id_counts.items() if count > 1}
    
    print(f"📊 Question ID Validation Report:")
    print(f"  Total question_ids found: {len(all_question_ids)}")
    print(f"  Unique question_ids: {len(set(all_question_ids))}")
    print(f"  Duplicates: {len(duplicates)}")
        
    if duplicates:
        print(f"\n⚠️  Duplicate question_ids found:")
        for qid, count in list(duplicates.items()): 
            print(f"    '{qid}': appears {count} times")
        
        if auto_delete_duplicates:
            print(f"\n🗑️  Auto-deleting duplicates...")
            
            # Group locations by question_id for efficient removal
            locations_by_id = {}
            for i, qid in enumerate(all_question_ids):
                if qid in duplicates:
                    if qid not in locations_by_id:
                        locations_by_id[qid] = []
                    locations_by_id[qid].append(question_locations[i])
            
            removed_count = 0
            for qid, locations in locations_by_id.items():
                # Sort alternative question removals by alt_idx in descending order
                # to avoid index shifting issues
                locations_to_remove = sorted(locations[1:], 
                                           key=lambda x: x.get("alt_idx", 0) if x["is_alternative"] else 0, 
                                           reverse=True)
                
                for location in locations_to_remove:
                    exam_data = content_data[location["exam"]]
                    skill = exam_data["skills_measured"][location["skill_idx"]]
                    subtopic = skill["subtopics"][location["subtopic_idx"]]
                    detail = subtopic["details"][location["detail_idx"]]
                    
                    if location["is_alternative"]:
                        # Remove from alternative_questions (safe with reverse order)
                        if location["alt_idx"] < len(detail.get("alternative_questions", [])):
                            detail["alternative_questions"].pop(location["alt_idx"])
                    else:
                        # Remove main question by setting question_id to None
                        detail["question_id"] = None
                        detail["question_text"] = None
                        detail["expected_answer"] = None
                    
                    removed_count += 1
            
            # Save cleaned content back to file
            with open(content_file, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Removed {removed_count} duplicate question_ids")
            print(f"✅ Cleaned content saved to {content_file}")
    else:
        print("✅ All question_ids are unique!")

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
