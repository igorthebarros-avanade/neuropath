#!/usr/bin/env python3
"""
Demo Azure Fundamentals QA Generator Script
Generates yes/no questions at the detail level with hash-based IDs.
"""

# Standard library imports
import os
import sys
import json
import time
import random
import hashlib
import argparse
from pathlib import Path

# Styling imports
from typing import Any

# Parallel processing imports
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# App-related services
from services.azure_ai_client import AzureAIClient
from prompts.prompts import DEMO_DETAIL_QA_GENERATION_PROMPT

# TODO: Remove after adding poetry as default environment manager
from dotenv import load_dotenv
load_dotenv()

# Adds parent directory to path for imports
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))


class DemoQAGenerator:
    """Generates demo yes/no questions for Azure fundamentals exams at detail level"""
    
    def __init__(self):
        # Sanity check: Only executes when in DEMO_MODE
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        if not self.demo_mode:
            raise ValueError("DEMO_MODE must be set to 'true' to run this script")
        
        # High-level Configuration settings (adjust as needed)
        self.MAX_WORKERS = int(os.getenv("MAX_WORKERS", "5"))
        self.MAX_TOKENS = 8192
        
        self.ai_client = AzureAIClient()
        self.scripts_dir = Path(__file__).parent.parent  # navigates to root level
        self.tmp_dir = self.scripts_dir / "tmp"
        self.tmp_dir.mkdir(exist_ok=True)
        
        # Loads existing content_updates.json file
        self.content_file = parent_dir / "content/content_updated.json"  # correct path to content file
        with open(self.content_file, 'r', encoding='utf-8') as f:
            self.content_data = json.load(f)
    
    def _generate_question_hash(self, question_text: str, exam_code: str, skill_area: str) -> str:
        """Generate hash-based question ID from question text"""
        # Creates a consistent hash from question text + context - Safe way to ensure uniqueness
        hash_input = f"{exam_code}_{skill_area}_{question_text}".lower().strip()
        hash_object = hashlib.md5(hash_input.encode())
        hash_hex = hash_object.hexdigest()[:8]  # Use first 8 characters
        
        skill_area_short = self._generate_skill_area_short(skill_area)
        return f"{exam_code.lower()}_{skill_area_short}_{hash_hex}"
    
    def _generate_skill_area_short(self, skill_area: str) -> str:
        """Generate short identifier for skill area. Used only for clearer readability"""
        words = skill_area.lower().replace("describe ", "").split()
        return "_".join(words[:3])
    
    def check_pending_work(self):
        """Check for any pending files in /tmp directory and merges if found."""
        pending_files = list(self.tmp_dir.glob("*.json"))
        if pending_files:
            print(f"Found {len(pending_files)} pending files. Merging...")
            for file_path in pending_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        pending_data = json.load(f)
                    self._merge_detail_questions(pending_data)
                    file_path.unlink()  # Removes after merging
                    print(f"Merged and removed: {file_path.name}")
                except Exception as e:
                    print(f"Error processing {file_path.name}: {e}")
    
    def _merge_detail_questions(self, new_data: dict[str, Any]):
        """Merge new questions at the detail-level into existing content structure"""
        for exam_code, exam_data in new_data.items():
            # Sanity check for exam code (i.e: won't processes unexisting exams)
            if exam_code not in self.content_data:
                continue
            
            for new_skill in exam_data.get("skills_measured", []):
                skill_area_name = new_skill["skill_area"]
                
                # Find matching skill area
                existing_skill = None
                for skill in self.content_data[exam_code]["skills_measured"]:
                    if skill["skill_area"] == skill_area_name:
                        existing_skill = skill
                        break
                
                if not existing_skill:
                    continue
                
                for new_subtopic in new_skill.get("subtopics", []):
                    topic_name = new_subtopic["topic"]
                    
                    # Find matching subtopic
                    existing_subtopic = None
                    for subtopic in existing_skill["subtopics"]:
                        if subtopic["topic"] == topic_name:
                            existing_subtopic = subtopic
                            break
                    
                    if existing_subtopic and "details" in new_subtopic:
                        # Convert old string-based details to new object-based structure
                        if isinstance(existing_subtopic.get("details", []), list) and \
                           len(existing_subtopic["details"]) > 0 and \
                           isinstance(existing_subtopic["details"][0], str):
                            # Legacy format - need to convert
                            print(f"Converting legacy details format for {topic_name}")
                            existing_subtopic["details"] = []
                        
                        # Merge new detail objects
                        if "details" not in existing_subtopic:
                            existing_subtopic["details"] = []
                        
                        existing_subtopic["details"].extend(new_subtopic["details"])
    
    # TODO: Review
    def generate_questions_for_detail(self, exam_code: str, skill_area: str, 
                                    topic_name: str, detail_text: str, 
                                    questions_count: int) -> dict:
        """Generate questions for a specific detail"""
        try:
            # Add artificial delay for realism - (e.g: simulating API call)
            time.sleep(random.uniform(0.5, 2))
            
            prompt = DEMO_DETAIL_QA_GENERATION_PROMPT.format(
                exam_code=exam_code,
                skill_area=skill_area,
                topic=topic_name,
                detail_text=detail_text,
                questions_count=questions_count
            )
            
            messages = [
                {"role": "system", "content": "You are an expert question generator for Microsoft Azure certification programs."},
                {"role": "user", "content": prompt}
            ]
            
            response = self.ai_client.call_chat_completion(
                messages=messages,
                max_tokens=self.MAX_TOKENS,
                temperature=0.7,       # Adjust temperature for creativity
                response_format={"type": "json_object"}
            )
            
            if response:
                questions_data = json.loads(response)
                generated_questions = questions_data.get("questions", [])
                
                # Generate hash-based IDs for questions
                for question in generated_questions:
                    question_text = question.get("question_text", "")
                    question["question_id"] = self._generate_question_hash(
                        question_text, exam_code, skill_area
                    )
                
                # Return detail object with embedded questions
                if generated_questions:
                    # Pick the best question (first one for now)
                    best_question = generated_questions[0]
                    return {
                        "description": detail_text,
                        "question_id": best_question["question_id"],
                        "question_text": best_question["question_text"],
                        "expected_answer": best_question["expected_answer"],
                        "skill_area": skill_area,
                        "alternative_questions": generated_questions[1:] if len(generated_questions) > 1 else []
                    }
            else:
                print(f"Failed to generate questions for detail: {detail_text[:50]}...")
                return {
                    "description": detail_text,
                    "question_id": None,
                    "question_text": None,
                    "expected_answer": None,
                    "skill_area": skill_area,
                    "alternative_questions": []
                }
                
        except Exception as e:
            print(f"Error generating questions for detail: {e}")
            return {
                "description": detail_text,
                "question_id": None,
                "question_text": None,
                "expected_answer": None,
                "skill_area": skill_area,
                "alternative_questions": []
            }
    
    def generate_questions_for_exam(self, exam_code: str, questions_per_detail: int = 3):
        """Generate questions for entire exam at detail level using parallel processing"""
        if exam_code not in self.content_data:
            raise ValueError(f"Exam code {exam_code} not found in content data")
        
        exam_data = self.content_data[exam_code]
        tasks = []
        
        # Prepare tasks for each detail
        for skill in exam_data["skills_measured"]:
            skill_area = skill["skill_area"]
            for subtopic in skill["subtopics"]:
                topic_name = subtopic["topic"]
                details = subtopic.get("details", [])
                
                # Handle both old (string) and new (object) formats
                for detail in details:
                    if isinstance(detail, str):
                        detail_text = detail
                    else:
                        # Skip if already processed
                        continue
                    
                    tasks.append({
                        "exam_code": exam_code,
                        "skill_area": skill_area,
                        "topic_name": topic_name,
                        "detail_text": detail_text,
                        "questions_count": questions_per_detail
                    })
        
        if not tasks:
            print(f"No details found to process for {exam_code}")
            return
        
        print(f"Generating questions for {exam_code} ({len(tasks)} details)")
        
        # Execute tasks in parallel
        results = {}
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            future_to_task = {
                executor.submit(
                    self.generate_questions_for_detail,
                    task["exam_code"],
                    task["skill_area"],
                    task["topic_name"],
                    task["detail_text"],
                    task["questions_count"]
                ): task for task in tasks
            }
            
            with tqdm(total=len(tasks), desc=f"Generating {exam_code} detail questions") as pbar:
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        detail_object = future.result()
                        
                        # Store interim results
                        safe_topic = task['topic_name'].replace(' ', '_').replace('/', '_')[:30]
                        interim_file = self.tmp_dir / f"{exam_code}_{safe_topic}_{hash(task['detail_text'])}.json"
                        
                        # Create structure for interim save
                        interim_data = {
                            exam_code: {
                                "skills_measured": [
                                    {
                                        "skill_area": task["skill_area"],
                                        "subtopics": [
                                            {
                                                "topic": task["topic_name"],
                                                "details": [detail_object]
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                        
                        with open(interim_file, 'w', encoding='utf-8') as f:
                            json.dump(interim_data, f, indent=2)
                        
                        # Store in results for final merge
                        if exam_code not in results:
                            results[exam_code] = {"skills_measured": []}
                        
                        # Find or create skill area
                        skill_found = False
                        for skill in results[exam_code]["skills_measured"]:
                            if skill["skill_area"] == task["skill_area"]:
                                # Find or create subtopic
                                subtopic_found = False
                                for subtopic in skill["subtopics"]:
                                    if subtopic["topic"] == task["topic_name"]:
                                        subtopic["details"].append(detail_object)
                                        subtopic_found = True
                                        break
                                
                                if not subtopic_found:
                                    skill["subtopics"].append({
                                        "topic": task["topic_name"],
                                        "details": [detail_object]
                                    })
                                skill_found = True
                                break
                        
                        if not skill_found:
                            results[exam_code]["skills_measured"].append({
                                "skill_area": task["skill_area"],
                                "subtopics": [{
                                    "topic": task["topic_name"],
                                    "details": [detail_object]
                                }]
                            })
                        
                    except Exception as e:
                        print(f"Error processing task: {e}")
                    
                    pbar.update(1)
        
        # Merge results into main content
        self._merge_detail_questions(results)
        
        # Clean up tmp files
        for tmp_file in self.tmp_dir.glob("*.json"):
            tmp_file.unlink()
        
        print(f"Successfully generated detail-level questions for {exam_code}")
    
    def save_content(self):
        """Save updated content back to file"""
        with open(self.content_file, 'w', encoding='utf-8') as f:
            json.dump(self.content_data, f, indent=2, ensure_ascii=False)
        print(f"Updated content saved to {self.content_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate demo questions for Azure fundamentals exams at detail level")
    parser.add_argument("--exam", required=True, choices=["AZ-900", "AI-900", "DP-900"],
                       help="Certification exam code")
    parser.add_argument("--questions-per-detail", type=int, default=3,
                       help="Number of questions to generate per detail (default: 3)")
    
    args = parser.parse_args()
    
    try:
        generator = DemoQAGenerator()
        
        # Check for pending work first
        generator.check_pending_work()
        
        # Generate new questions
        generator.generate_questions_for_exam(args.exam, args.questions_per_detail)
        
        # Save results
        generator.save_content()
        
        print(f"Detail-level question generation completed for {args.exam}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()