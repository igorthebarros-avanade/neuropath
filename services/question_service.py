# question_service.py
import json
import random
from pathlib import Path
from collections import defaultdict
from services.exam_data_loader import ExamDataLoader
from services.azure_ai_client import AzureAIClient
from prompts.prompts import * 
import os

class QuestionService:
    def __init__(self, exam_data_loader: ExamDataLoader, ai_client: AzureAIClient):
        self.exam_data_loader = exam_data_loader
        self.ai_client = ai_client
        self.files_dir = Path("files")
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        
        # Default question counts per exam type
        self.exam_defaults = {
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

    def get_exam_defaults(self, exam_code: str) -> dict:
        """Get default question counts for a specific exam."""
        return self.exam_defaults.get(exam_code, self.exam_defaults["default"])

    def _generate_questions_live(self, selected_exam_code, num_yes_no, num_qualitative):
        """Original live question generation using Azure OpenAI"""
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

            output_file = self.files_dir / f"questions_{selected_exam_code}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(questions_data, f, indent=2)
            print(f"Successfully generated and saved questions to {output_file}")

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from API response during question generation: {e}")
            print(f"Raw response content: {response_content}")
        except Exception as e:
            print(f"An unexpected error occurred during question generation: {e}.")

    def _stratified_sample_questions(self, questions_by_skill, total_requested: int) -> list:
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
            # Return all questions if we need more than available
            all_questions = []
            for questions in questions_by_skill.values():
                all_questions.extend(questions)
            return all_questions
        
        selected_questions = []
        
        # Calculate base allocation per skill area
        base_per_skill = max(1, total_requested // len(skill_areas))
        remaining = total_requested - (base_per_skill * len(skill_areas))
        
        # First pass: allocate base amount to each skill area
        for skill_area in skill_areas:
            available_in_skill = len(questions_by_skill[skill_area])
            to_sample = min(base_per_skill, available_in_skill)
            
            if to_sample > 0:
                sampled = random.sample(questions_by_skill[skill_area], to_sample)
                selected_questions.extend(sampled)
                
                # Remove sampled questions to avoid duplicates
                for q in sampled:
                    questions_by_skill[skill_area].remove(q)
        
        # Second pass: distribute remaining questions to skill areas with available questions
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

    def _load_precomputed_questions(self, selected_exam_code, num_yes_no, num_qualitative):
        """Load precomputed questions with stratified sampling (for DEMO mode)"""
        print(f"Generating diagnostic questions for {selected_exam_code} (Yes/No: {num_yes_no}, Qualitative: {num_qualitative})...")
        
        # Load content data
        content_file = Path("content/content_updated.json")
        if not content_file.exists():
            print("Error: content_updated.json not found. Cannot load precomputed questions.")
            return
            
        with open(content_file, 'r', encoding='utf-8') as f:
            content_data = json.load(f)
        
        if selected_exam_code not in content_data:
            print(f"Error: Exam {selected_exam_code} not found in content data.")
            return
        
        # Extract and organize precomputed questions by skill area
        questions_by_skill = defaultdict(list)
        exam_data = content_data[selected_exam_code]
        
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
        
        total_available = sum(len(questions) for questions in questions_by_skill.values())
        
        if total_available == 0:
            print(f"No precomputed questions found for {selected_exam_code}")
            return
            
        # Adjust request if we don't have enough questions
        if total_available < (num_yes_no + num_qualitative):
            print(f"Warning: Only {total_available} precomputed questions available. Adjusting request.")
            num_yes_no = min(num_yes_no, total_available)
            num_qualitative = 0  # Demo mode only has yes/no questions
        
        # Perform stratified sampling for yes/no questions
        selected_questions = self._stratified_sample_questions(questions_by_skill, num_yes_no)
        
        # Generate basic qualitative questions if requested (one per skill area)
        qualitative_questions = []
        if num_qualitative > 0:
            unique_skill_areas = list(set([q["skill_area"] for q in selected_questions]))
            for i, skill_area in enumerate(unique_skill_areas[:num_qualitative]):
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
        
        # Combine and save
        questions_data = {
            "exam_code": selected_exam_code,
            "questions": selected_questions + qualitative_questions
        }
        
        # Print sampling summary
        skill_distribution = defaultdict(int)
        for q in selected_questions:
            skill_distribution[q["skill_area"]] += 1
            
        print(f"Stratified sampling results:")
        for skill_area, count in skill_distribution.items():
            print(f"  {skill_area}: {count} questions")
        
        output_file = self.files_dir / f"questions_{selected_exam_code}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(questions_data, f, indent=2)
        
        print(f"Successfully loaded and saved {len(questions_data['questions'])} questions to {output_file}")
    
    def generate_diagnostic_questions(self, selected_exam_code, num_yes_no=None, num_qualitative=None):
        """
        Generates diagnostic questions for the selected exam.
        Uses exam-specific defaults if counts not provided.
        """
        # Use exam-specific defaults if not provided
        if num_yes_no is None or num_qualitative is None:
            defaults = self.get_exam_defaults(selected_exam_code)
            num_yes_no = num_yes_no or defaults["yes_no"]
            num_qualitative = num_qualitative or defaults["qualitative"]
        
        if self.demo_mode:
            self._load_precomputed_questions(selected_exam_code, num_yes_no, num_qualitative)
        else:
            self._generate_questions_live(selected_exam_code, num_yes_no, num_qualitative)