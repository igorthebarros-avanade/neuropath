# image_generation_service.py
from pathlib import Path
from services.azure_ai_client import AzureAIClient
from prompts.prompts import *
import os # For os.path.basename
import requests # For downloading the image
from utils.utils import *

class ImageGenerationService:
    def __init__(self, ai_client: AzureAIClient): # Correct __init__ signature
        self.ai_client = ai_client
        self.files_dir = Path("files")
        self.images_output_dir = self.files_dir / "images"
        self.images_output_dir.mkdir(parents=True, exist_ok=True) # Ensure images subdirectory exists

    def generate_coloring_images(
        self,
        concepts: list,
        style_choice: str,
        exam_code: str,
        size: str = "1024x1024",
        quality: str = "standard",
    ):
        """
        Generates coloring book images for the given concepts based on a chosen style.

        Args:
            concepts (list): A list of concise concept strings.
            style_choice (str): The chosen drawing style (e.g., "Simple Line Art", "Architectural Blueprint").
            exam_code (str): The exam code to use in the filename.
        """
        if not concepts:
            print("No concepts provided for image generation.")
            return

        print(f"\nGenerating coloring images for concepts related to {exam_code} in '{style_choice}' style...")

        # Map user-friendly style choice to DALL-E 'style' parameter and prompt modifiers
        dalle_style_param = "vivid" # Default DALL-E style
        prompt_modifier = ""
        if style_choice == "Simple Line Art":
            prompt_modifier = "simple line art, cartoon style, bold black and white outline, no shading, no fill, coloring book page, "
            dalle_style_param = "natural" # Natural often gives cleaner lines
        elif style_choice == "Architectural Blueprint":
            prompt_modifier = "architectural blueprint style, technical diagram, isometric view, black and white outline, no shading, no fill, coloring book page, "
            dalle_style_param = "natural"
        elif style_choice == "Nature/Everyday Analogy":
            prompt_modifier = "simple line art, analogy, nature-inspired, everyday object, black and white outline, no shading, no fill, coloring book page, "
            dalle_style_param = "natural"
        elif style_choice == "Character/Mascot-Driven":
            prompt_modifier = "friendly cartoon character interacting with, simple line drawing, mascot style, black and white outline, no shading, no fill, coloring book page, "
            dalle_style_param = "vivid" # Vivid can make characters pop more
        elif style_choice == "Abstract Geometric/Flowchart":
            prompt_modifier = "abstract geometric shapes, flowchart style, interconnected forms, black and white outline, no shading, no fill, coloring book page, "
            dalle_style_param = "natural"

        generated_image_urls = []

        for i, concept in enumerate(concepts):
            print(f"  Generating image for concept: '{concept}' ({i+1}/{len(concepts)})")
            
            # Use AI to generate a more detailed image description from the concept
            image_description_messages = [
                {"role": "system", "content": "You are an AI assistant that generates concise image descriptions for coloring book pages."},
                {"role": "user", "content": prompts.IMAGE_DESCRIPTION_PROMPT.format(concepts_text=concept)}
            ]
            image_description = self.ai_client.call_chat_completion(
                messages=image_description_messages,
                max_tokens=200, # Sufficient for a concise description
                temperature=0.7
            )

            if not image_description:
                print(f"    Could not generate image description for '{concept}'. Skipping.")
                continue

            # Combine the generic prompt modifier with the specific image description
            full_image_prompt = f"{prompt_modifier}{image_description}. Suitable for a child's coloring book."
            
            # Call DALL-E to generate the image
            image_url = self.ai_client.generate_image(
                prompt=full_image_prompt,
                style=dalle_style_param,
                size=size,
                quality=quality,
            )

            if image_url:
                generated_image_urls.append({"concept": concept, "url": image_url})
                print(f"    Generated image URL for '{concept}': {image_url}")
                
                # Download the image
                try:
                    response = requests.get(image_url)
                    response.raise_for_status() # Raise an exception for HTTP errors
                    # Sanitize concept for filename
                    safe_concept = "".join(c for c in concept if c.isalnum() or c in [' ', '_']).replace(' ', '_')[:50]
                    image_filename = self.images_output_dir / f"{exam_code}_{safe_concept}_{i+1}.png"
                    with open(image_filename, 'wb') as f:
                        f.write(response.content)
                    print(f"    Image saved to '{image_filename}'")
                except requests.exceptions.RequestException as req_err:
                    print(f"    Error downloading image from {image_url}: {req_err}")
                except Exception as e:
                    print(f"    Error saving image file: {e}")
            else:
                print(f"    Failed to generate image for '{concept}'.")
        
        if generated_image_urls:
            print(f"\nSuccessfully generated and saved {len(generated_image_urls)} coloring images to '{self.images_output_dir}'.")
        else:
            print("\nNo coloring images were generated.")

    def _validate_image_client(self) -> bool:
        """Ensure the Azure OpenAI image client is configured."""
        if not self.ai_client or not self.ai_client.image_client:
            print("Image generation endpoint is not configured correctly. Check your .env settings.")
            return False
        print(f"Using image endpoint: {self.ai_client.endpoint_image}")
        return True

    def _select_style(self) -> str:
        """Interactively select an image style."""
        styles = [
            "Simple Line Art",
            "Architectural Blueprint",
            "Nature/Everyday Analogy",
            "Character/Mascot-Driven",
            "Abstract Geometric/Flowchart",
        ]
        for idx, style in enumerate(styles, 1):
            print(f"{idx}. {style}")
        choice = input("Select a style (1-5): ")
        try:
            index = int(choice) - 1
            if 0 <= index < len(styles):
                return styles[index]
        except ValueError:
            pass
        print("Invalid style choice. Defaulting to 'Simple Line Art'.")
        return "Simple Line Art"

    def run_image_studio(self):
        """Interactive loop for previewing and batch generating images."""
        if not self._validate_image_client():
            return

        while True:
            print("\nImage Generation Studio:")
            print("1. Generate Preview")
            print("2. Batch Generate")
            print("3. Exit")
            choice = input("Enter your choice: ")

            if choice == "1":
                concept = input("Enter a concept for the preview image: ").strip()
                if not concept:
                    print("Concept cannot be empty.")
                    continue
                style = self._select_style()
                size = input("Image size [1024x1024]: ").strip() or "1024x1024"
                quality = input("Quality [standard]: ").strip() or "standard"
                self.generate_coloring_images([concept], style, "preview", size=size, quality=quality)
            elif choice == "2":
                concepts_raw = input("Enter concepts separated by commas: ")
                concepts = [c.strip() for c in concepts_raw.split(",") if c.strip()]
                if not concepts:
                    print("No valid concepts provided.")
                    continue
                style = self._select_style()
                size = input("Image size [1024x1024]: ").strip() or "1024x1024"
                quality = input("Quality [standard]: ").strip() or "standard"
                exam_code = input("Exam code for filenames [batch]: ").strip() or "batch"
                self.generate_coloring_images(concepts, style, exam_code, size=size, quality=quality)
            elif choice == "3":
                print("Exiting Image Generation Studio.")
                break
            else:
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    ai_client = AzureAIClient()
    service = ImageGenerationService(ai_client)
    service.run_image_studio()

