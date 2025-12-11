"""Gemini API Service for AI responses."""
from typing import Optional
import google.generativeai as genai


class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self):
        """Initialize Gemini Service."""
        self.model_name = "gemini-2.5-flash"
        self.model = None
        print(" GeminiService initialized (not yet configured)")
    
    def configure(self, api_key: str) -> bool:
        """Configure Gemini API with API key."""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
            print(f" Gemini API configured")
            return True
        except Exception as e:
            print(f" Failed to configure Gemini API: {e}")
            return False
    
    def get_response(self, prompt: str) -> Optional[str]:
        """Get response from Gemini API."""
        if not self.model:
            print(" Gemini API not configured")
            return None
        
        try:
            print(" Sending prompt to Gemini API...")
            response = self.model.generate_content(prompt)
            gemini_text = response.text
            print(f" Gemini response received")
            return gemini_text
        except Exception as e:
            print(f" Error getting Gemini response: {e}")
            return f"Error: {str(e)}"
