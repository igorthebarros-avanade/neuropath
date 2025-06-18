# podcast_generation_service.py

from pathlib import Path
import os # For os.path.basename



from pathlib import Path
from services.azure_ai_client import AzureAIClient
from prompts.prompts import *
import os # For os.path.basename
import requests # For downloading the image
from utils.utils import *


class PodcastGenerationService:
    def __init__(self, ai_client: AzureAIClient):
        self.ai_client = ai_client
        self.files_dir = Path("files")
        self.podcasts_output_dir = self.files_dir / "podcasts"
        self.podcasts_output_dir.mkdir(parents=True, exist_ok=True) # Ensure podcasts subdirectory exists

    def generate_podcast(self, concepts: list, exam_code: str):
        """
        Generates a podcast (audio file) explaining the given concepts.

        Args:
            concepts (list): A list of concise concept strings.
            exam_code (str): The exam code to use in the filename.
        """
        if not concepts:
            print("No concepts provided for podcast generation.")
            return

        print(f"\nGenerating podcast for concepts related to {exam_code}...")

        # Generate the full script for all concepts
        concepts_text = "\n".join([f"- {c}" for c in concepts])
        podcast_script_messages = [
            {"role": "system", "content": "You are an AI assistant that generates concise and engaging podcast scripts."},
            {"role": "user", "content": prompts.PODCAST_SCRIPT_PROMPT.format(concepts_text=concepts_text)}
        ]
        full_script = self.ai_client.call_chat_completion(
            messages=podcast_script_messages,
            max_tokens=2000, # Allow more tokens for the script
            temperature=0.7
        )

        if not full_script:
            print("Could not generate podcast script. Aborting podcast generation.")
            return

        print("\nGenerated Podcast Script:")
        print(full_script)

        # Generate audio from the script
        audio_content = self.ai_client.generate_audio(text=full_script)

        if audio_content:
            podcast_filename = self.podcasts_output_dir / f"{exam_code}_concepts_podcast.mp3"
            try:
                with open(podcast_filename, 'wb') as f:
                    f.write(audio_content)
                print(f"\nPodcast successfully generated and saved to '{podcast_filename}'.")
            except Exception as e:
                print(f"Error saving podcast file: {e}")
        else:
            print("\nFailed to generate audio for the podcast.")

