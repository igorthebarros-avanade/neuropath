# question_service.py - Refactored version
import json
import random
from pathlib import Path
from collections import defaultdict
from services.exam_data_loader import ExamDataLoader
from services.azure_ai_client import AzureAIClient
from prompts.prompts import *
from utils.utils import stratified_sample_questions
import os

# TODO: Update as new exams are added or agree on overall heuristics for defaults
# Configuration constants
EXAM_DEFAULTS = {
    # Fundamentals exams
    "AZ-900": {"yes_no": 15, "qualitative": 5},
    "AI-900": {"yes_no": 12, "qualitative": 4}, 
    "DP-900": {"yes_no": 12, "qualitative": 4},
    # Associate level
    "AZ-104": {"yes_no": 25, "qualitative": 10},
    "AZ-204": {"yes_no": 25, "qualitative": 10},
    # Expert level  
    "AZ-305": {"yes_no": 35, "qualitative": 15},
    # Default for unknown exams
    "default": {"yes_no": 20, "qualitative": 8}
}

class QuestionService:
    def __init__(self, exam_data_loader: ExamDataLoader, ai_client: AzureAIClient):
        self.exam_data_loader = exam_data_loader
        self.ai_client = ai_client
        self.files_dir = Path("files")
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        self.content_file = Path(os.getenv("EXAM_DATA_JSON_PATH", "content/content_updated.json"))

    def get_exam_defaults(self, exam_code: str) -> dict:
        """Get default question counts for a specific exam."""
        return EXAM_DEFAULTS.get(exam_code, EXAM_DEFAULTS["default"])

    def _load_content_data(self) -> dict:
        """Load content data from the configured file."""
        if not self.content_file.exists():
            raise FileNotFoundError(f"Content file not found at {self.content_file}")
            
        with open(self.content_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _extract_questions_from_content(self, exam_code: str) -> dict:
        """Extract and organize questions by skill area from content data."""
        content_data = self._load_content_data()
        
        if exam_code not in content_data:
            raise ValueError(f"Exam {exam_code} not found in content data.")
        
        questions_by_skill = defaultdict(list)
        exam_data = content_data[exam_code]
        
        for skill in exam_data["skills_measured"]:
            skill_area = skill["skill_area"]
            for subtopic in skill["subtopics"]:
                details = subtopic.get("details", [])
                for detail in details:
                    if isinstance(detail, dict) and detail.get("question_text"):
                        question = {
                            "type": "yes_no",
                            "skill_area": skill_area,
                            "question": detail["question_text"],
                            "expected_answer": detail["expected_answer"],
                            "purpose": "Binary Assessment"
                        }
                        questions_by_skill[skill_area].append(question)
        
        return questions_by_skill

    def _save_questions_to_file(self, questions_data: dict, exam_code: str) -> Path:
        """Save questions data to JSON file."""
        output_file = self.files_dir / f"questions_{exam_code}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(questions_data, f, indent=2)
        return output_file

    def _generate_qualitative_questions(self, skill_areas: list, num_qualitative: int) -> list:
        """Generate basic qualitative questions for given skill areas."""
        qualitative_questions = []
        for i, skill_area in enumerate(skill_areas[:num_qualitative]):
            qualitative_questions.append({
                "type": "qualitative",
                "skill_area": skill_area,
                "question": f"Explain the key concepts and benefits of {skill_area.lower()}.",
                "purpose": "Scaled Assessment",
                "scoring_criteria": [
                    "Demonstrates understanding of core concepts",
                    "Explains practical applications", 
                    "Mentions key benefits or features",
                    "Uses appropriate technical terminology",
                    "Provides clear and organized explanation"
                ]
            })
        return qualitative_questions

    def _print_sampling_summary(self, questions: list):
        """Print stratified sampling results summary."""
        skill_distribution = defaultdict(int)
        for q in questions:
            skill_distribution[q["skill_area"]] += 1
            
        print(f"Stratified sampling results:")
        for skill_area, count in skill_distribution.items():
            print(f"  {skill_area}: {count} questions")

    def _generate_questions_live(self, selected_exam_code, num_yes_no, num_qualitative):
        """Live question generation using Azure OpenAI"""
        print(f"Generating diagnostic questions for {selected_exam_code} (Yes/No: {num_yes_no}, Qualitative: {num_qualitative})...")

        context = self.exam_data_loader.prepare_context(detail_level="full", exam_codes=[selected_exam_code])
        if not context:
            print(f"Error: Could not prepare context for exam {selected_exam_code}. Aborting question generation.")
            return

        question_generation_instructions = QUESTION_GENERATION_INSTRUCTIONS.format(
            num_yes_no=num_yes_no, num_qualitative=num_qualitative
        )

        messages = [
            {
                "role": "system",
                "content": "You are an expert on Microsoft Azure certification exams and a question generator. Your task is to create diagnostic questions in a precise JSON format based on provided exam content. You MUST include the 'skill_area' for each generated question."
            },
            {
                "role": "user",
                "content": f"{question_generation_instructions}\n\nExam Data for {selected_exam_code}:\n{context}"
            }
        ]

        try:
            response_content = self.ai_client.call_chat_completion(
                messages=messages,
                max_tokens=8192,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            if response_content is None:
                print("API call failed or returned empty content.")
                return

            questions_data = json.loads(response_content)
            questions_data["exam_code"] = selected_exam_code

            output_file = self._save_questions_to_file(questions_data, selected_exam_code)
            print(f"Successfully generated and saved questions to {output_file}")

            return questions_data

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from API response during question generation: {e}")
            print(f"Raw response content: {response_content}")
        except Exception as e:
            print(f"An unexpected error occurred during question generation: {e}.")

    def _load_precomputed_questions(self, selected_exam_code, num_yes_no, num_qualitative):
        """Load precomputed questions with stratified sampling (for DEMO mode)"""
        print(f"Generating diagnostic questions for {selected_exam_code} (Yes/No: {num_yes_no}, Qualitative: {num_qualitative})...")
        
        try:
            questions_by_skill = self._extract_questions_from_content(selected_exam_code)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return
        
        total_available = sum(len(questions) for questions in questions_by_skill.values())
        
        if total_available == 0:
            print(f"No precomputed questions found for {selected_exam_code}")
            return
            
        # Adjust request if insufficient questions
        if total_available < (num_yes_no + num_qualitative):
            print(f"Warning: Only {total_available} precomputed questions available. Adjusting request.")
            num_yes_no = min(num_yes_no, total_available)
            num_qualitative = 0  # Demo mode only has yes/no questions
        
        # Perform stratified sampling
        selected_questions = stratified_sample_questions(questions_by_skill, num_yes_no)
        
        # Generate qualitative questions if requested
        qualitative_questions = []
        if num_qualitative > 0:
            unique_skill_areas = list(set([q["skill_area"] for q in selected_questions]))
            qualitative_questions = self._generate_qualitative_questions(unique_skill_areas, num_qualitative)
        
        # Combine and save
        questions_data = {
            "exam_code": selected_exam_code,
            "questions": selected_questions + qualitative_questions
        }
        
        self._print_sampling_summary(selected_questions)
        
        output_file = self._save_questions_to_file(questions_data, selected_exam_code)
        print(f"Successfully loaded and saved {len(questions_data['questions'])} questions to {output_file}")
    
    def generate_diagnostic_questions(self, selected_exam_code, num_yes_no=None, num_qualitative=None):
        """Generate diagnostic questions for the selected exam."""
        if num_yes_no is None or num_qualitative is None:
            defaults = self.get_exam_defaults(selected_exam_code)
            num_yes_no = num_yes_no or defaults["yes_no"]
            num_qualitative = num_qualitative or defaults["qualitative"]
        
        if self.demo_mode:
            self._load_precomputed_questions(selected_exam_code, num_yes_no, num_qualitative)
        else:
            return self._generate_questions_live(selected_exam_code, num_yes_no, num_qualitative)