"""Gemini 2.5 Pro client with safe fallbacks."""

import os
import json
from pathlib import Path
from typing import Optional
import google.generativeai as genai


def get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key from environment variable or api_keys.json."""
    # Try environment variable first
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key
    
    # Try api_keys.json file
    try:
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        api_keys_path = project_root / "api_keys.json"
        
        if api_keys_path.exists():
            with open(api_keys_path, 'r') as f:
                keys = json.load(f)
                api_key = keys.get("GEMINI_API_KEY")
                if api_key:
                    return api_key
    except Exception:
        pass
    
    return None


def call_gemini(system_prompt: str, user_prompt: str, timeout: int = 30) -> str:
    """
    Call Gemini 2.5 Pro with system and user prompts.
    
    Returns:
        Response text as string
        
    Raises:
        ValueError: If API key is missing or call fails
    """
    api_key = get_gemini_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment or api_keys.json")
    
    try:
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.5 Pro
        model = genai.GenerativeModel("gemini-2.5-pro")
        
        # Combine prompts
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        response = model.generate_content(
            full_prompt,
            request_options={"timeout": timeout * 1000}  # Convert to milliseconds
        )
        
        return response.text
        
    except Exception as e:
        raise ValueError(f"Gemini API error: {str(e)}")
