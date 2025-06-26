#!/usr/bin/env python3
"""
Demo Azure Fundamentals QA Generator Script

This script generates yes/no questions at the granular detail level for Azure certification
exams, using AI to create contextually relevant questions from exam content structure.

Key Features:
- Parallel processing for efficient question generation
- Hash-based unique question IDs to prevent duplicates
- Intermediate file storage for recovery from interruptions
- Automatic merging of questions into existing content structure

Usage:
    python demo_fundamentals_qa_generator.py --exam AZ-900 --questions-per-detail 3

Environment Variables Required:
    DEMO_MODE=true (safety check to prevent accidental execution)
    MAX_WORKERS=3 (optional, controls parallel processing threads)
    
Dependencies:
    - Azure OpenAI API client configured
    - Content file with exam structure at content/content_updated.json
"""

# Future Enhancement Opportunities:
# - Add question deduplication logic to prevent semantically similar questions
# - Extend support for qualitative questions beyond yes/no format  
# - Implement dynamic content structure discovery instead of manual mapping
# - Consider asyncio instead of ThreadPoolExecutor for better I/O performance
# - Add support for associate-level exams (AI-102, AZ-104, etc.)

# Standard library imports
import os
import sys
import json
import time
import random
import hashlib
import argparse
from pathlib import Path
from typing import Any, Dict, List, Set, Optional

# Third-party imports for parallel processing and progress tracking
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Application-specific imports
from services.azure_ai_client import AzureAIClient
from prompts.prompts import DEMO_DETAIL_QA_GENERATION_PROMPT

# TODO: Remove this when poetry is leveraged
# Environment setup for development
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to Python path for service imports
current_directory = Path(__file__).resolve().parent
parent_directory = current_directory.parent
sys.path.append(str(parent_directory))


class DemoQAGenerator:
    """
    Generates demonstration yes/no questions for Azure fundamentals certification exams.
    
    This class processes exam content at the detail level, creating contextually appropriate
    questions that test specific facts and concepts. It uses parallel processing to handle
    large content volumes efficiently and implements recovery mechanisms for long-running
    operations.
    
    Attributes:
        demo_mode (bool): Safety flag ensuring intentional execution in demo environment
        max_parallel_workers (int): Number of concurrent threads for question generation
        max_ai_tokens (int): Token limit for AI model requests
        ai_client (AzureAIClient): Client for Azure OpenAI API interactions
        temp_directory (Path): Directory for storing intermediate processing files
        content_file_path (Path): Path to the main exam content JSON file
        exam_content_data (dict): Loaded exam content structure and details
    
    Example:
        >>> generator = DemoQAGenerator()
        >>> generator.generate_questions_for_exam("AZ-900", questions_per_detail=3)
        >>> generator.save_content()
    """
    
    # Configuration constants
    DEFAULT_MAX_WORKERS = 3
    DEFAULT_QUESTIONS_PER_DETAIL = 3
    AI_TOKEN_LIMIT = 8192
    QUESTION_ID_HASH_LENGTH = 8
    ARTIFICIAL_DELAY_RANGE = (0.5, 2.0)  # Seconds to simulate realistic API timing
    
    def __init__(self):
        """
        Initialize the QA generator with environment validation and content loading.
        
        Raises:
            ValueError: If DEMO_MODE is not enabled or content file is missing
            FileNotFoundError: If content_updated.json cannot be located
        """
        # Safety mechanism: Only executes in explicit demo environment
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        if not self.demo_mode:
            raise ValueError(
                "DEMO_MODE environment variable must be set to 'true' to run this script. "
                "This prevents accidental execution in production environments."
            )
        
        # Parallel processing configuration
        self.max_parallel_workers = int(os.getenv("MAX_WORKERS", self.DEFAULT_MAX_WORKERS))
        self.max_ai_tokens = self.AI_TOKEN_LIMIT
        
        # Initialize Azure OpenAI client for question generation
        self.ai_client = AzureAIClient()
        
        # Directory structure setup
        self.scripts_directory = Path(__file__).parent
        self.temp_directory = self.scripts_directory / "tmp"
        self.temp_directory.mkdir(exist_ok=True)
        
        # Load exam content structure from JSON file
        self.content_file_path = self.scripts_directory.parent / "content/content_updated.json"
        try:
            with open(self.content_file_path, 'r', encoding='utf-8') as content_file:
                self.exam_content_data = json.load(content_file)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Exam content file not found at {self.content_file_path}. "
                "Ensure content_updated.json exists in the content directory."
            )
    
    def _generate_unique_question_identifier(self, question_text: str, exam_code: str, 
                                        skill_area: str, topic_name: str, 
                                        detail_description: str) -> str:
        """
        Generate a unique, deterministic identifier for a question using content hashing.
        
        This method creates consistent IDs that prevent duplicate questions while remaining
        readable and traceable. The hash is based on question content and context.
        
        Args:
            question_text (str): The actual question text content
            exam_code (str): Certification exam identifier (e.g., "AZ-900")
            skill_area (str): Skill domain the question belongs to
            topic_name (str): Specific topic within the skill area
            detail_description (str): Additional context for the question
        
        Returns:
            str: Unique question identifier in format: {exam}_{skill_short}_{hash}
            
        Example:
            >>> generator._generate_unique_question_identifier(
            ...     "Does Azure Blob Storage store relational data?", 
            ...     "AZ-900", 
            ...     "Describe Azure storage services"
            ... )
            'az_900_describe_azure_storage_3f7a8b2c'
        """
        normalized_input = f"{exam_code}_{skill_area}_{topic_name}_{detail_description}_{question_text}".lower().strip()
        content_hash = hashlib.md5(normalized_input.encode()).hexdigest()
        truncated_hash = content_hash[:self.QUESTION_ID_HASH_LENGTH]
        
        skill_abbreviation = self._create_skill_area_abbreviation(skill_area)
        
        return f"{exam_code.lower()}_{skill_abbreviation}_{truncated_hash}"
    
    def _create_skill_area_abbreviation(self, skill_area: str) -> str:
        """
        Create a concise abbreviation for skill area names to improve readability.
        
        Removes common prefixes and takes the first few meaningful words to create
        a shorter identifier suitable for question IDs.
        
        Args:
            skill_area (str): Full skill area name from exam content
            
        Returns:
            str: Abbreviated skill area identifier
            
        Example:
            >>> generator._create_skill_area_abbreviation("Describe Azure storage services")
            'azure_storage_services'
            >>> generator._create_skill_area_abbreviation("Describe cloud concepts") 
            'cloud_concepts'
        """
        # Remove common prefixes to focus on core concepts
        cleaned_area = skill_area.lower().replace("describe ", "")
        meaningful_words = cleaned_area.split()
        
        # Take first 3 words to balance readability and brevity
        return "_".join(meaningful_words[:3])
    
    def check_and_process_pending_work(self) -> None:
        """
        Identify and merge any unprocessed temporary files from previous interrupted runs.
        
        This recovery mechanism ensures that partial work from interrupted generation
        sessions is not lost. It automatically detects, merges, and cleans up temporary
        files from the /tmp directory.
        
        Example workflow:
            1. Previous run was interrupted during processing
            2. Temporary files remain in /tmp directory  
            3. This method detects them and merges into main content
            4. Temporary files are removed after successful merge
        """
        pending_file_paths = list(self.temp_directory.glob("*.json"))
        
        if not pending_file_paths:
            print("No pending work found in temporary directory.")
            return
            
        print(f"Found {len(pending_file_paths)} pending files from previous run. Processing...")
        
        successfully_processed = 0
        for temp_file_path in pending_file_paths:
            try:
                with open(temp_file_path, 'r', encoding='utf-8') as temp_file:
                    pending_question_data = json.load(temp_file)
                
                # Merge the pending data into main content structure  
                self._merge_generated_questions_into_content(pending_question_data)
                
                # Clean up successfully processed file
                temp_file_path.unlink()
                successfully_processed += 1
                print(f"✓ Merged and removed: {temp_file_path.name}")
                
            except Exception as processing_error:
                print(f"✗ Error processing {temp_file_path.name}: {processing_error}")
        
        print(f"Successfully processed {successfully_processed} pending files.")
    
    def _merge_generated_questions_into_content(self, new_question_data: Dict[str, Any]) -> None:
        """
        Integrate newly generated questions into the existing content structure.
        
        This method handles the complex merging logic to incorporate new questions
        while preserving existing content organization. It supports both new questions
        and alternative questions for existing content.
        
        Args:
            new_question_data (Dict[str, Any]): Generated question data in content format
                Expected structure:
                {
                    "exam_code": {
                        "skills_measured": [
                            {
                                "skill_area": "...",
                                "subtopics": [
                                    {
                                        "topic": "...",
                                        "details": [question_objects]
                                    }
                                ]
                            }
                        ]
                    }
                }
        """
        for exam_code, new_exam_data in new_question_data.items():
            if exam_code not in self.exam_content_data:
                print(f"Warning: Exam code {exam_code} not found in existing content. Skipping.")
                continue
            
            for new_skill_data in new_exam_data.get("skills_measured", []):
                skill_area_name = new_skill_data["skill_area"]
                
                # Find matching skill area in existing content
                matching_existing_skill = self._find_skill_area_in_content(exam_code, skill_area_name)
                if not matching_existing_skill:
                    print(f"Warning: Skill area '{skill_area_name}' not found. Skipping.")
                    continue
                
                # Process each subtopic within the skill area
                for new_subtopic_data in new_skill_data.get("subtopics", []):
                    topic_name = new_subtopic_data["topic"]
                    
                    # Find matching subtopic in existing skill area
                    matching_existing_subtopic = self._find_subtopic_in_skill(
                        matching_existing_skill, topic_name
                    )
                    
                    if matching_existing_subtopic and "details" in new_subtopic_data:
                        self._merge_detail_questions(matching_existing_subtopic, new_subtopic_data)
    
    def _find_skill_area_in_content(self, exam_code: str, skill_area_name: str) -> Optional[Dict]:
        """
        Locate a specific skill area within the exam content structure.
        
        Args:
            exam_code (str): Exam identifier to search within
            skill_area_name (str): Name of skill area to find
            
        Returns:
            Optional[Dict]: Skill area data if found, None otherwise
        """
        for skill_data in self.exam_content_data[exam_code]["skills_measured"]:
            if skill_data["skill_area"] == skill_area_name:
                return skill_data
        return None
    
    def _find_subtopic_in_skill(self, skill_data: Dict, topic_name: str) -> Optional[Dict]:
        """
        Locate a specific subtopic within a skill area.
        
        Args:
            skill_data (Dict): Skill area data to search within  
            topic_name (str): Name of subtopic to find
            
        Returns:
            Optional[Dict]: Subtopic data if found, None otherwise
        """
        for subtopic_data in skill_data["subtopics"]:
            if subtopic_data["topic"] == topic_name:
                return subtopic_data
        return None
    
    def _merge_detail_questions(self, existing_subtopic: Dict, new_subtopic_data: Dict) -> None:
        """
        Merge new question details into an existing subtopic structure.
        
        This handles the complex logic of matching questions to existing details
        and organizing them as main questions vs. alternative questions.
        
        Args:
            existing_subtopic (Dict): Existing subtopic to merge into
            new_subtopic_data (Dict): New subtopic data containing questions
        """
        if "details" not in existing_subtopic:
            existing_subtopic["details"] = []
        
        for new_detail_with_question in new_subtopic_data["details"]:
            detail_description = new_detail_with_question.get("description", "")
            
            # Find existing detail with matching description
            matching_existing_detail = self._find_detail_by_description(
                existing_subtopic["details"], detail_description
            )
            
            if matching_existing_detail:
                # Add new question as alternative to existing detail
                self._add_alternative_question(matching_existing_detail, new_detail_with_question)
            else:
                # This is a completely new detail - add it to the list
                existing_subtopic["details"].append(new_detail_with_question)
    
    def _find_detail_by_description(self, detail_list: List, target_description: str) -> Optional[Dict]:
        """
        Find a detail object by its description text.
        
        Args:
            detail_list (List): List of detail objects to search
            target_description (str): Description to match against
            
        Returns:
            Optional[Dict]: Matching detail object if found, None otherwise
        """
        for detail_item in detail_list:
            if isinstance(detail_item, dict) and detail_item.get("description") == target_description:
                return detail_item
        return None
    
    def _add_alternative_question(self, existing_detail: Dict, new_question_detail: Dict) -> None:
        """
        Add a new question as an alternative to an existing detail.
        
        Args:
            existing_detail (Dict): Existing detail to add alternative to
            new_question_detail (Dict): New question detail to add as alternative
        """
        if "alternative_questions" not in existing_detail:
            existing_detail["alternative_questions"] = []
        
        # Add the main question from new detail as an alternative
        if new_question_detail.get("question_text"):
            new_alternative = {
                "question_id": new_question_detail.get("question_id"),
                "question_text": new_question_detail.get("question_text"),
                "expected_answer": new_question_detail.get("expected_answer")
            }
            existing_detail["alternative_questions"].append(new_alternative)
        
        # Also add any existing alternatives from the new detail
        existing_detail["alternative_questions"].extend(
            new_question_detail.get("alternative_questions", [])
        )
    
    def generate_questions_for_specific_detail(self, exam_code: str, skill_area: str, 
                                             topic_name: str, detail_description: str, 
                                             target_question_count: int) -> Dict[str, Any]:
        """
        Generate multiple questions for a single detail using AI, with error handling.
        
        This method calls the Azure OpenAI API to generate contextually relevant
        yes/no questions based on specific detail content. It includes artificial
        delays to simulate realistic API usage patterns and avoid rate limiting.
        
        Args:
            exam_code (str): Certification exam identifier (e.g., "AZ-900")
            skill_area (str): Skill domain for context
            topic_name (str): Specific topic within the skill area  
            detail_description (str): The specific detail text to generate questions about
            target_question_count (int): How many questions to generate
            
        Returns:
            Dict[str, Any]: Detail object with embedded questions and alternatives
                Structure:
                {
                    "description": "Original detail text",
                    "question_id": "Unique identifier for best question", 
                    "question_text": "Main question text",
                    "expected_answer": "Yes|No",
                    "skill_area": "Skill area name",
                    "alternative_questions": [list of additional questions]
                }
                
        Example:
            >>> detail_obj = generator.generate_questions_for_specific_detail(
            ...     "AZ-900", 
            ...     "Describe Azure storage services",
            ...     "Azure Blob Storage",
            ...     "Object serverless storage optimized for storing massive amounts of unstructured data",
            ...     3
            ... )
            >>> print(detail_obj["question_text"])
            "Does Azure Blob Storage primarily store unstructured data?"
        """
        try:
            # Add artificial delay to simulate realistic API timing and avoid rate limits
            delay_seconds = random.uniform(*self.ARTIFICIAL_DELAY_RANGE)
            time.sleep(delay_seconds)
            
            # Construct AI prompt with specific context
            ai_generation_prompt = DEMO_DETAIL_QA_GENERATION_PROMPT.format(
                exam_code=exam_code,
                skill_area=skill_area,
                topic=topic_name,
                detail_text=detail_description,
                questions_count=target_question_count
            )
            
            # Prepare messages for AI conversation
            conversation_messages = [
                {
                    "role": "system", 
                    "content": "You are an expert question generator for Microsoft Azure certification programs."
                },
                {
                    "role": "user", 
                    "content": ai_generation_prompt
                }
            ]
            
            # Make API call to generate questions
            ai_response = self.ai_client.call_chat_completion(
                messages=conversation_messages,
                max_tokens=self.max_ai_tokens,
                temperature=0.7,  # Balance creativity with consistency
                response_format={"type": "json_object"}
            )
            
            if ai_response:
                question_response_data = json.loads(ai_response)
                generated_questions = question_response_data.get("questions", [])
                
                # Generate unique IDs for all questions
                for question_item in generated_questions:
                    question_text = question_item.get("question_text", "")
                    unique_id = self._generate_unique_question_identifier(
                        question_text, exam_code, skill_area, topic_name, detail_description
                    )
                    question_item["question_id"] = unique_id
                
                # Structure the response with best question and alternatives
                if generated_questions:
                    primary_question = generated_questions[0]  # Use first as primary
                    alternative_questions = generated_questions[1:] if len(generated_questions) > 1 else []
                    
                    return {
                        "description": detail_description,
                        "question_id": primary_question["question_id"],
                        "question_text": primary_question["question_text"],
                        "expected_answer": primary_question["expected_answer"],
                        "skill_area": skill_area,
                        "alternative_questions": alternative_questions
                    }
            
            # Handle case where AI response was empty or invalid
            print(f"Warning: Failed to generate questions for detail: {detail_description[:50]}...")
            return self._create_empty_detail_object(detail_description, skill_area)
                
        except Exception as generation_error:
            print(f"Error generating questions for detail: {generation_error}")
            return self._create_empty_detail_object(detail_description, skill_area)
    
    def _create_empty_detail_object(self, detail_description: str, skill_area: str) -> Dict[str, Any]:
        """
        Create a detail object with no questions for error cases.
        
        Args:
            detail_description (str): The detail text that failed processing
            skill_area (str): Associated skill area
            
        Returns:
            Dict[str, Any]: Empty detail object structure
        """
        return {
            "description": detail_description,
            "question_id": None,
            "question_text": None,
            "expected_answer": None,
            "skill_area": skill_area,
            "alternative_questions": []
        }
    
    def generate_questions_for_entire_exam(self, exam_code: str, 
                                         questions_per_detail: int = DEFAULT_QUESTIONS_PER_DETAIL) -> None:
        """
        Generate questions for an entire exam using parallel processing for efficiency.
        
        This method orchestrates the complete question generation workflow:
        1. Extracts all unique details from exam content
        2. Creates parallel tasks for each detail  
        3. Processes tasks using ThreadPoolExecutor
        4. Saves intermediate results for recovery
        5. Merges final results into main content structure
        
        Args:
            exam_code (str): Certification exam to process (e.g., "AZ-900", "AI-900")
            questions_per_detail (int): Number of questions to generate per detail
            
        Raises:
            ValueError: If exam_code is not found in content data
            
        Example:
            >>> generator = DemoQAGenerator()
            >>> generator.generate_questions_for_entire_exam("AZ-900", 3)
            Generating questions for AZ-900 (45 details)
            Generating AZ-900 detail questions: 100%|████████| 45/45 [00:30<00:00,  1.50it/s]
            Successfully generated detail-level questions for AZ-900
        """
        if exam_code not in self.exam_content_data:
            raise ValueError(f"Exam code {exam_code} not found in content data")
        
        exam_structure = self.exam_content_data[exam_code]
        processing_tasks = []
        processed_detail_descriptions: Set[str] = set()
        
        # Extract all unique detail descriptions to prevent duplicate processing
        for skill_area_data in exam_structure["skills_measured"]:
            skill_area_name = skill_area_data["skill_area"]
            
            for subtopic_data in skill_area_data["subtopics"]:
                topic_name = subtopic_data["topic"]
                detail_items = subtopic_data.get("details", [])
                
                for detail_item in detail_items:
                    detail_text = self._extract_detail_text(detail_item)
                    
                    # Only process unique detail descriptions
                    if detail_text and detail_text not in processed_detail_descriptions:
                        processed_detail_descriptions.add(detail_text)
                        processing_tasks.append({
                            "exam_code": exam_code,
                            "skill_area": skill_area_name,
                            "topic_name": topic_name,
                            "detail_text": detail_text,
                            "questions_count": questions_per_detail
                        })
        
        if not processing_tasks:
            print(f"No details found to process for {exam_code}")
            return
        
        print(f"Generating questions for {exam_code} ({len(processing_tasks)} unique details)")
        
        # Execute tasks in parallel with progress tracking
        aggregated_results = {}
        with ThreadPoolExecutor(max_workers=self.max_parallel_workers) as executor:
            # Submit all tasks to the executor
            future_to_task_mapping = {
                executor.submit(
                    self.generate_questions_for_specific_detail,
                    task["exam_code"],
                    task["skill_area"], 
                    task["topic_name"],
                    task["detail_text"],
                    task["questions_count"]
                ): task for task in processing_tasks
            }
            
            # Process completed tasks with progress bar
            with tqdm(total=len(processing_tasks), desc=f"Generating {exam_code} detail questions") as progress_bar:
                for completed_future in as_completed(future_to_task_mapping):
                    task_info = future_to_task_mapping[completed_future]
                    
                    try:
                        generated_detail_object = completed_future.result()
                        
                        # Save intermediate results for recovery
                        self._save_intermediate_result(task_info, generated_detail_object)
                        
                        # Aggregate results for final merge
                        self._aggregate_task_result(aggregated_results, task_info, generated_detail_object)
                        
                    except Exception as task_error:
                        print(f"Error processing task for {task_info['topic_name']}: {task_error}")
                    
                    progress_bar.update(1)
        
        # Merge all aggregated results into main content
        self._merge_generated_questions_into_content(aggregated_results)
        
        # Clean up temporary files after successful merge
        self._cleanup_temporary_files()
        
        print(f"Successfully generated detail-level questions for {exam_code}")
    
    def _extract_detail_text(self, detail_item: Any) -> str:
        """
        Extract text content from a detail item regardless of its format.
        
        Detail items can be either strings or dictionaries with description fields.
        
        Args:
            detail_item: The detail item to extract text from
            
        Returns:
            str: The detail text content, or empty string if not extractable
        """
        if isinstance(detail_item, str):
            return detail_item
        elif isinstance(detail_item, dict):
            return detail_item.get("description", "")
        else:
            return ""
    
    def _save_intermediate_result(self, task_info: Dict, detail_object: Dict) -> None:
        """
        Save intermediate processing results to temporary files for recovery.
        
        Args:
            task_info (Dict): Information about the processed task
            detail_object (Dict): Generated detail object with questions
        """
        # Create safe filename from topic name
        safe_topic_name = task_info['topic_name'].replace(' ', '_').replace('/', '_')[:30]
        detail_hash = hash(task_info['detail_text'])
        temp_filename = f"{task_info['exam_code']}_{safe_topic_name}_{detail_hash}.json"
        temp_file_path = self.temp_directory / temp_filename
        
        # Create structured data for saving
        intermediate_data = {
            task_info['exam_code']: {
                "skills_measured": [{
                    "skill_area": task_info["skill_area"],
                    "subtopics": [{
                        "topic": task_info["topic_name"],
                        "details": [detail_object]
                    }]
                }]
            }
        }
        
        # Save to temporary file
        with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
            json.dump(intermediate_data, temp_file, indent=2)
    
    def _aggregate_task_result(self, results_dict: Dict, task_info: Dict, detail_object: Dict) -> None:
        """
        Aggregate individual task results into a unified structure for final merging.
        
        Args:
            results_dict (Dict): Accumulator for all results
            task_info (Dict): Information about the current task
            detail_object (Dict): Generated detail object to aggregate
        """
        exam_code = task_info['exam_code']
        skill_area = task_info['skill_area']
        topic_name = task_info['topic_name']
        
        # Initialize exam structure if needed
        if exam_code not in results_dict:
            results_dict[exam_code] = {"skills_measured": []}
        
        # Find or create skill area
        target_skill = None
        for skill in results_dict[exam_code]["skills_measured"]:
            if skill["skill_area"] == skill_area:
                target_skill = skill
                break
        
        if not target_skill:
            target_skill = {"skill_area": skill_area, "subtopics": []}
            results_dict[exam_code]["skills_measured"].append(target_skill)
        
        # Find or create subtopic
        target_subtopic = None
        for subtopic in target_skill["subtopics"]:
            if subtopic["topic"] == topic_name:
                target_subtopic = subtopic
                break
        
        if not target_subtopic:
            target_subtopic = {"topic": topic_name, "details": []}
            target_skill["subtopics"].append(target_subtopic)
        
        # Add the detail object
        target_subtopic["details"].append(detail_object)
    
    def _cleanup_temporary_files(self) -> None:
        """Remove all temporary files after successful processing."""
        for temp_file in self.temp_directory.glob("*.json"):
            temp_file.unlink()
    
    def save_updated_content_to_file(self) -> None:
        """
        Persist the updated exam content with generated questions back to the JSON file.
        
        This method writes the complete updated content structure back to the original
        content file, preserving all existing data while adding the newly generated questions.
        
        Example:
            >>> generator = DemoQAGenerator()
            >>> generator.generate_questions_for_entire_exam("AZ-900")
            >>> generator.save_updated_content_to_file()
            Updated content saved to /path/to/content/content_updated.json
        """
        try:
            with open(self.content_file_path, 'w', encoding='utf-8') as content_file:
                json.dump(
                    self.exam_content_data, 
                    content_file, 
                    indent=2, 
                    ensure_ascii=False  # Preserve Unicode characters for international content
                )
            print(f"Updated content saved to {self.content_file_path}")
            
        except Exception as save_error:
            print(f"Error saving content to file: {save_error}")
            raise


def main():
    """
    Main entry point for the demo QA generator script.
    
    Handles command-line argument parsing, validates inputs, and orchestrates
    the complete question generation workflow with proper error handling.
    """
    argument_parser = argparse.ArgumentParser(
        description="Generate demo yes/no questions for Azure fundamentals exams at detail level",
        epilog="Example: python demo_fundamentals_qa_generator.py --exam AZ-900 --questions-per-detail 3"
    )
    
    argument_parser.add_argument(
        "--exam", 
        required=True, 
        choices=["AZ-900", "AI-900", "DP-900"],
        help="Certification exam code to generate questions for"
    )
    
    argument_parser.add_argument(
        "--questions-per-detail", 
        type=int, 
        default=DemoQAGenerator.DEFAULT_QUESTIONS_PER_DETAIL,
        help=f"Number of questions to generate per detail (default: {DemoQAGenerator.DEFAULT_QUESTIONS_PER_DETAIL})"
    )
    
    parsed_arguments = argument_parser.parse_args()
    
    try:
        # Initialize the generator with validation
        question_generator = DemoQAGenerator()
        
        # Process any pending work from previous interrupted runs
        question_generator.check_and_process_pending_work()
        
        # Generate new questions for the specified exam
        question_generator.generate_questions_for_entire_exam(
            parsed_arguments.exam, 
            parsed_arguments.questions_per_detail
        )
        
        # Persist results to file
        question_generator.save_updated_content_to_file()
        
        print(f"\n✓ Detail-level question generation completed successfully for {parsed_arguments.exam}")
        print(f"✓ Generated {parsed_arguments.questions_per_detail} questions per detail")
        
    except Exception as execution_error:
        print(f"✗ Error during execution: {execution_error}")
        sys.exit(1)


if __name__ == "__main__":
    main()