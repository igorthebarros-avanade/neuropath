# azure_ai_client.py
from openai import AzureOpenAI
import os
from pathlib import Path
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from typing import Literal, Optional

VALID_SIZES = {"auto","1024x1024","1536x1024","1024x1536","256x256","512x512","1792x1024","1024x1792"}
VALID_QUALITIES = {"standard", "hd", "low", "medium", "high", "auto"} 
VALID_STYLES = {"vivid", "natural"}

class AzureAIClient:
    def __init__(self,
                 endpoint_text_audio_whisper=None, api_key_text_audio_whisper=None,
                 endpoint_image=None, api_key_image=None,
                 api_version=None,
                 deployment_text=None, deployment_image=None, deployment_audio=None, deployment_whisper=None):
        
        # --- Endpoint and API Key Configuration ---
        self.endpoint_text_audio_whisper = endpoint_text_audio_whisper if endpoint_text_audio_whisper else os.getenv("AZURE_OPENAI_ENDPOINT_TEXT_AUDIO_WHISPER")
        self.api_key_text_audio_whisper = api_key_text_audio_whisper if api_key_text_audio_whisper else os.getenv("AZURE_OPENAI_API_KEY_TEXT_AUDIO_WHISPER")
        
        self.endpoint_image = endpoint_image if endpoint_image else os.getenv("AZURE_OPENAI_ENDPOINT_IMAGE")
        self.api_key_image = api_key_image if api_key_image else os.getenv("AZURE_OPENAI_API_KEY_IMAGE")

        self.api_version = api_version if api_version else os.getenv("AZURE_OPENAI_API_VERSION")
        
        # --- Deployment Names ---
        self.deployment_text = deployment_text if deployment_text else os.getenv("AZURE_OPENAI_DEPLOYMENT_TEXT")
        self.deployment_image = deployment_image if deployment_image else os.getenv("AZURE_OPENAI_DEPLOYMENT_IMAGE")
        self.deployment_audio = deployment_audio if deployment_audio else os.getenv("AZURE_OPENAI_DEPLOYMENT_AUDIO")
        self.deployment_whisper = deployment_whisper if deployment_whisper else os.getenv("AZURE_OPENAI_DEPLOYMENT_WHISPER")

        # --- Client Instances ---
        self.text_audio_whisper_client = None
        self.image_client = None
        self._initialize_clients()

    def _initialize_clients(self):
        """Initializes separate Azure OpenAI clients for different endpoints."""
        # Initialize client for Text, Audio (TTS), Whisper (STT)
        if self.endpoint_text_audio_whisper and self.api_key_text_audio_whisper:
            try:
                self.text_audio_whisper_client = AzureOpenAI(
                    azure_endpoint=self.endpoint_text_audio_whisper,
                    api_key=self.api_key_text_audio_whisper,
                    api_version=self.api_version
                )
            except Exception as e:
                print(f"Error initializing Text/Audio/Whisper client: {e}")
                self.text_audio_whisper_client = None
        else:
            print("Warning: Text/Audio/Whisper endpoint or API key not configured. Text, TTS, and Whisper features may not work.")

        # Initialize client for Image (DALL-E 3)
        if self.endpoint_image and self.api_key_image:
            try:
                self.image_client = AzureOpenAI(
                    azure_endpoint=self.endpoint_image,
                    api_key=self.api_key_image,
                    api_version=self.api_version
                )
            except Exception as e:
                print(f"Error initializing Image client: {e}")
                self.image_client = None
        else:
            print("Warning: Image endpoint or API key not configured. Image generation may not work.")
        
        # Raise error if no client can be initialized for essential functions
        if not self.text_audio_whisper_client and not self.image_client:
             raise ValueError("No Azure OpenAI clients could be initialized. Check your .env configuration.")


    # Apply retry decorator to API calls
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5),
           retry=retry_if_exception_type(Exception))
    def call_chat_completion(self, messages, max_tokens, temperature, response_format=None):
        """
        Makes a chat completion call to the Azure OpenAI API using the text deployment.
        Uses the text_audio_whisper_client.
        """
        if not self.text_audio_whisper_client:
            print("Text/Audio/Whisper client not initialized. Cannot make chat completion call.")
            return None
        
        if not self.deployment_text:
            raise ValueError("Deployment name is not set for text model.")
        
        if not response_format:
            raise ValueError("Response format must be specified for chat completions.")
        
        try:
            completion = self.text_audio_whisper_client.chat.completions.create(
                model=self.deployment_text,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format=response_format
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"An error occurred during text API call (retrying): {e}")
            raise

    # Apply retry decorator to API calls
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5),
           retry=retry_if_exception_type(Exception))
    def generate_image(self, prompt: str, style: Literal["vivid", "natural"] = "vivid",
                        size: Literal["auto", "1024x1024", "1536x1024", "1024x1536","256x256", "512x512", "1792x1024", "1024x1792" ] = "1024x1024",
                        quality: Literal["standard", "hd", "low", "medium", "high", "auto"] = "standard"):
        """
        Generates an image using the DALL-E model via Azure OpenAI.
        Uses the image_client.
        """
        if not self.image_client:
            print("Image client not initialized. Cannot generate image.")
            return None
        
        if not self.deployment_image:
            print("Azure OpenAI image deployment name not configured. Cannot generate image.")
            return None

        if size not in VALID_SIZES:
           raise ValueError(f"Invalid image size: {size}")
        
        if quality not in VALID_QUALITIES:
            raise ValueError(f"Invalid image quality: {quality}")
        
        if style not in VALID_STYLES:
            raise ValueError(f"Invalid image style: {style}")

        try:
            response = self.image_client.images.generate( # Use image_client
                model=self.deployment_image,
                prompt=prompt,
                n=1,
                size=size,
                quality=quality,
                style=style
            )

            if response.data is not None:
                return response.data[0].url
            
            else:
                print("Result is type is None and it can't be accessible.")
                raise 

        except Exception as e:
            print(f"An error occurred during image generation API call (retrying): {e}")
            raise

    # Apply retry decorator to API calls
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5),
           retry=retry_if_exception_type(Exception))
    def generate_audio(self, text: str, voice: str = "alloy"):
        """
        Generates audio from text using the Text-to-Speech (TTS) model via Azure OpenAI.
        Uses the text_audio_whisper_client.
        """
        if not self.text_audio_whisper_client:
            print("Text/Audio/Whisper client not initialized. Cannot generate audio.")
            return None
        if not self.deployment_audio:
            print("Azure OpenAI audio deployment name not configured. Cannot generate audio.")
            return None

        try:
            response = self.text_audio_whisper_client.audio.speech.create( # Use text_audio_whisper_client
                model=self.deployment_audio,
                voice=voice,
                input=text
            )
            return response.content
        except Exception as e:
            print(f"An error occurred during audio generation API call (retrying): {e}")
            raise

    # Apply retry decorator to API calls
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5),
           retry=retry_if_exception_type(Exception))
    def translate_audio(self, audio_file_path: Path):
        """
        Translates audio from a file using the Whisper model via Azure OpenAI.
        Uses the text_audio_whisper_client.
        """
        if not self.text_audio_whisper_client:
            print("Text/Audio/Whisper client not initialized. Cannot translate audio.")
            return None
        if not self.deployment_whisper:
            print("Azure OpenAI Whisper deployment name not configured. Cannot translate audio.")
            return None
        if not audio_file_path.exists():
            print(f"Error: Audio file not found at {audio_file_path}")
            return None

        try:
            with open(audio_file_path, "rb") as audio_file:
                response = self.text_audio_whisper_client.audio.translations.create( # Use text_audio_whisper_client
                    model=self.deployment_whisper,
                    file=audio_file
                )
                return response.text
        except Exception as e:
            print(f"An error occurred during audio translation API call (retrying): {e}")
            raise
