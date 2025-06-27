import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import os

@dataclass
class SimulationQuestion:
    type: str
    skill_area: str
    question: str
    expected_answer: Optional[str] = None
    scoring_criteria: Optional[str] = None

@dataclass
class SimulationResult:
    exam_code: str
    timestamp: str
    sampling_method: str
    questions_attempted: List[Dict]
    total_questions: int
    
class SimulationWebService:
    def __init__(self):
        self.files_dir = Path("files")
        self.current_simulation = None
        self.questions = []
        self.current_question_index = 0
        self.sampling_method = "unknown"
        
    def get_available_question_files(self) -> List[Path]:
        """Returns a list of available question files."""
        return list(self.files_dir.glob('questions_*.json'))
    
    def load_questions(self, file_path: Path) -> Tuple[bool, str]:
        """
        Loads questions from the selected file with enhanced validation.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
            
            self.exam_code = questions_data.get("exam_code", "Unknown Exam")
            raw_questions = questions_data.get("questions", [])
            
            if not raw_questions:
                return False, f"No questions found in {file_path.name}"
            
            # Detect sampling method
            demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
            self.sampling_method = "stratified" if demo_mode else "ai_generated"
            
            # Convert to structured objects
            self.questions = [
                SimulationQuestion(
                    type=q['type'],
                    skill_area=q.get('skill_area', 'N/A'),
                    question=q['question'],
                    expected_answer=q.get('expected_answer'),
                    scoring_criteria=q.get('scoring_criteria')
                ) for q in raw_questions
            ]
            
            # Initialize new simulation
            self.current_simulation = {
                "exam_code": self.exam_code,
                "timestamp": datetime.now().isoformat(),
                "sampling_method": self.sampling_method,
                "questions_attempted": []
            }
            self.current_question_index = 0
            
            # Provide sampling summary
            if self.sampling_method == "stratified":
                skill_distribution = {}
                for q in self.questions:
                    skill_area = q.skill_area
                    skill_distribution[skill_area] = skill_distribution.get(skill_area, 0) + 1
                
                distribution_msg = "Stratified sampling distribution: " + ", ".join([f"{k}: {v}" for k, v in skill_distribution.items()])
                return True, f"Loaded {len(self.questions)} questions for {self.exam_code}. {distribution_msg}"
            else:
                return True, f"Loaded {len(self.questions)} AI-generated questions for {self.exam_code}"
            
        except Exception as e:
            return False, f"Error loading questions: {str(e)}"
    
    def generate_demo_questions(self, exam_code: str, num_questions: int, question_service) -> Tuple[bool, str]:
        """
        Generate demo questions using stratified sampling.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Use the enhanced question service to generate stratified questions
            question_service._load_precomputed_questions(exam_code, num_questions, 0)
            
            # Load the generated file
            temp_file = self.files_dir / f"questions_{exam_code}.json"
            if temp_file.exists():
                return self.load_questions(temp_file)
            else:
                return False, "Failed to generate demo questions"
                
        except Exception as e:
            return False, f"Error generating demo questions: {str(e)}"
    
    def get_current_question(self) -> Optional[SimulationQuestion]:
        """Returns the current question."""
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
    
    def get_simulation_progress(self) -> Dict:
        """Returns information about the simulation progress."""
        return {
            "current_question": self.current_question_index + 1,
            "total_questions": len(self.questions),
            "exam_code": getattr(self, 'exam_code', 'Unknown'),
            "sampling_method": self.sampling_method,
            "is_complete": self.current_question_index >= len(self.questions)
        }
    
    def get_skill_distribution(self) -> Dict[str, int]:
        """Returns the distribution of questions by skill area."""
        distribution = {}
        for q in self.questions:
            skill_area = q.skill_area
            distribution[skill_area] = distribution.get(skill_area, 0) + 1
        return distribution
    
    def go_back_one_question(self) -> bool:
        """
        Goes back one question in the simulation.
        
        Returns:
            bool: True if it was possible to go back, False if already at the first question
        """
        if self.current_question_index > 0:
            self.current_question_index -= 1
            return True
        return False
    
    def submit_answer(self, answer: str) -> bool:
        """
        Submits an answer for the current question.
        
        Returns:
            bool: True if the answer was successfully processed
        """
        if not self.current_simulation or self.current_question_index >= len(self.questions):
            return False
        
        current_q = self.questions[self.current_question_index]
        
        result_entry = {
            "question_number": self.current_question_index + 1,
            "type": current_q.type,
            "skill_area": current_q.skill_area,
            "question": current_q.question,
            "user_answer": answer.strip(),
            "user_score": None
        }
        
        if current_q.type == "yes_no":
            result_entry["expected_answer"] = current_q.expected_answer
        elif current_q.type == "qualitative":
            result_entry["scoring_criteria"] = current_q.scoring_criteria
        
        self.current_simulation["questions_attempted"].append(result_entry)
        self.current_question_index += 1
        
        return True
    
    def save_simulation_results(self) -> Tuple[bool, str]:
        """
        Saves the simulation results.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not self.current_simulation:
            return False, "No simulation data to save"
        
        try:
            exam_code = self.current_simulation["exam_code"]
            results_file = self.files_dir / f"{exam_code}_results.json"
            
            # Load existing results
            all_results = []
            if results_file.exists():
                try:
                    with open(results_file, 'r', encoding='utf-8') as f:
                        all_results = json.load(f)
                except json.JSONDecodeError:
                    all_results = []
            
            # Add current simulation
            all_results.append(self.current_simulation)
            
            # Save file
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2)
            
            return True, f"Results saved to {results_file.name}"
            
        except Exception as e:
            return False, f"Error saving results: {str(e)}"
    
    def reset_simulation(self):
        """Resets the simulation state."""
        self.current_simulation = None
        self.questions = []
        self.current_question_index = 0
        self.sampling_method = "unknown"