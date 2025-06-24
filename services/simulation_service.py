# simulation_service.py
import os
import json
from pathlib import Path
from datetime import datetime

class SimulationService:
    def __init__(self):
        self.files_dir = Path("files") # Define the files directory

    def conduct_simulation(self, results_file_suffix="results.json"):
        """
        Prompts the user with questions and stores their answers.
        Handles both "live" and demo mode question formats.
        """
        question_files = list(self.files_dir.glob('questions_*.json'))
        if not question_files:
            print("No question files found. Please generate questions first using option 1.")
            return

        print("\nAvailable Question Files for Simulation:")
        for i, file_path in enumerate(question_files):
            print(f"{i + 1}. {file_path.name}")

        selected_file_path = None
        while True:
            try:
                choice = input("Enter the number of the question file you want to use for simulation: ")
                selected_index = int(choice) - 1
                if 0 <= selected_index < len(question_files):
                    selected_file_path = question_files[selected_index]
                    print(f"You selected: {selected_file_path.name}")
                    break
                else:
                    print("Invalid number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        questions_source_file = str(selected_file_path)
        selected_exam_code = selected_file_path.stem.replace("questions_", "")
        results_file = self.files_dir / f"{selected_exam_code}_{results_file_suffix}"

        try:
            with open(questions_source_file, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Questions file '{questions_source_file}' not found.")
            return
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{questions_source_file}'. File might be corrupted.")
            return

        exam_code = questions_data.get("exam_code", "Unknown Exam")
        questions = questions_data.get("questions", [])
        
        # Filter questions based on demo mode if applicable
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        if demo_mode:
            original_count = len(questions)
            questions = [q for q in questions if q.get('type') == 'yes_no']
            if len(questions) < original_count:
                print(f"Note: Demo mode filtered out {original_count - len(questions)} qualitative questions.")

        if not questions:
            print(f"No questions found in '{questions_source_file}' for exam {exam_code}.")
            return

        print(f"\n--- Starting Simulation for Exam: {exam_code} ---")
        current_simulation_results = {
            "exam_code": exam_code,
            "timestamp": datetime.now().isoformat(),
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
