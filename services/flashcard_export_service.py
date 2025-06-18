# flashcard_export_service.py
import csv
from pathlib import Path

class FlashcardExportService:
    def __init__(self):
        self.files_dir = Path("files") # Ensure this matches your main.py's files_dir

    def export_to_csv(self, structured_exam_content: list, output_filename="flashcards.csv"):
        """
        Exports structured exam content (skill areas and subtopics) to a CSV file
        in "Question, Answer" format, suitable for flashcard applications.

        Args:
            structured_exam_content (list): A list of dictionaries, where each dict has
                                            'question' and 'answer' keys, representing concepts.
            output_filename (str): The name of the CSV file to create (e.g., "AZ-900_flashcards.csv").
        """
        if not structured_exam_content:
            print("No structured exam content provided for flashcard export.")
            return

        output_file_path = self.files_dir / output_filename
        
        try:
            with open(output_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Question', 'Answer']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for item in structured_exam_content:
                    writer.writerow({
                        'Question': item.get('question', 'N/A'),
                        'Answer': item.get('answer', 'N/A')
                    })
            print(f"Flashcards successfully exported to '{output_file_path}'")
        except Exception as e:
            print(f"Error exporting flashcards to CSV: {e}")

