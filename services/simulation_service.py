import os
import json
from pathlib import Path
from datetime import datetime

class SimulationService:
    def __init__(self):
        self.files_dir = Path("files")
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"

    def get_available_question_files(self):
        """Get available question files with better formatting."""
        question_files = list(self.files_dir.glob('questions_*.json'))
        
        if not question_files:
            return []
            
        # Enhanced display with question count and generation method
        formatted_files = []
        for file_path in question_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                exam_code = data.get("exam_code", "Unknown")
                question_count = len(data.get("questions", []))
                
                # Detect if stratified sampling was used (demo mode indicator)
                method = "Stratified Sampling" if self.demo_mode else "AI Generated"
                
                formatted_files.append({
                    'file': file_path,
                    'display': f"{exam_code} ({question_count} questions, {method})",
                    'exam_code': exam_code,
                    'count': question_count
                })
            except:
                formatted_files.append({
                    'file': file_path,
                    'display': file_path.name,
                    'exam_code': 'Unknown',
                    'count': 0
                })
        
        return formatted_files

    def conduct_simulation(self, results_file_suffix="results.json"):
        """Enhanced simulation with better file selection and demo mode support."""
        
        # Check for existing files
        formatted_files = self.get_available_question_files()
        if not formatted_files:
            print("No question files found. Please generate questions first using option 1.")
            return

        print("\nAvailable Question Files for Simulation:")
        for i, file_info in enumerate(formatted_files):
            print(f"{i + 1}. {file_info['display']}")

        # File selection
        selected_file_path = None
        while True:
            try:
                choice = input("Enter the number of the question file you want to use for simulation: ")
                selected_index = int(choice) - 1
                if 0 <= selected_index < len(formatted_files):
                    selected_file_path = formatted_files[selected_index]['file']
                    print(f"You selected: {formatted_files[selected_index]['display']}")
                    break
                else:
                    print("Invalid number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # Load and validate questions
        try:
            with open(selected_file_path, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Questions file '{selected_file_path}' not found.")
            return
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{selected_file_path}'. File might be corrupted.")
            return

        exam_code = questions_data.get("exam_code", "Unknown Exam")
        questions = questions_data.get("questions", [])
        
        # Demo mode filtering
        if self.demo_mode:
            original_count = len(questions)
            questions = [q for q in questions if q.get('type') == 'yes_no']
            if len(questions) < original_count:
                print(f"Note: Demo mode filtered out {original_count - len(questions)} qualitative questions.")

        if not questions:
            print(f"No questions found in '{selected_file_path}' for exam {exam_code}.")
            return

        # Show sampling info if available
        if self.demo_mode:
            skill_distribution = {}
            for q in questions:
                skill_area = q.get('skill_area', 'Unknown')
                skill_distribution[skill_area] = skill_distribution.get(skill_area, 0) + 1
            
            print(f"\nQuestion distribution by skill area:")
            for skill, count in skill_distribution.items():
                print(f"  {skill}: {count} questions")

        # Conduct simulation
        selected_exam_code = questions_data.get("exam_code", "Unknown")
        results_file = self.files_dir / f"{selected_exam_code}_{results_file_suffix}"

        print(f"\n--- Starting Simulation for Exam: {exam_code} ---")
        current_simulation_results = {
            "exam_code": exam_code,
            "timestamp": datetime.now().isoformat(),
            "sampling_method": "stratified" if self.demo_mode else "ai_generated",
            "questions_attempted": []
        }

        for i, q in enumerate(questions):
            print(f"\nQuestion {i + 1} ({q['type'].replace('_', ' ').title()} - Category: {q.get('skill_area', 'N/A')}):")
            print(q['question'])

            user_answer = input("Your answer: ").strip()

            result_entry = {
                "type": q['type'],
                "skill_area": q.get('skill_area', 'N/A'),
                "question": q['question'],
                "user_answer": user_answer,
                "user_score": None
            }
            
            if q['type'] == "yes_no":
                result_entry["expected_answer"] = q.get("expected_answer")
            elif q['type'] == "qualitative":
                result_entry["scoring_criteria"] = q.get("scoring_criteria")
            
            current_simulation_results["questions_attempted"].append(result_entry)

        print(f"\n--- Simulation for Exam: {exam_code} Complete! ---")
        
        # Save results
        all_results = []
        if results_file.exists():
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    all_results = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Existing '{results_file}' is corrupted. Starting a new results file.")
                all_results = []
        
        all_results.append(current_simulation_results)

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2)
        print(f"Simulation results saved to '{results_file}'.")