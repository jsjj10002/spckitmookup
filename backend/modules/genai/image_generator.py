"""
Google GenAI (Imagen) Image Generator Module
============================================

Generates 3D visualization of PC builds using Google's GenAI models (Gemini 3 Pro Image Preview).
"""

import os
import base64
from typing import List, Dict, Any, Optional
from loguru import logger
# Updated Import per user request
from google import genai
from google.genai import types

class ImageGenerator:
    """Generation of PC build images using Google GenAI (v2 SDK)"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GenAI client
        
        Args:
            api_key: Google Cloud API Key
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY or GOOGLE_API_KEY not found. Image generation will be disabled.")
            self.client = None
        else:
            try:
                # Initialize client using new SDK pattern
                self.client = genai.Client(
                    api_key=self.api_key,
                )
                logger.info("Google GenAI Client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize GenAI Client: {e}")
                self.client = None

    def generate_pc_image(self, components: List[Dict[str, Any]], purpose: str = "gaming") -> Optional[bytes]:
        """
        Generate a 3D image of the PC build based on components.
        
        Args:
            components: List of selected components with 'name', 'category'
            purpose: Usage purpose (e.g., 'gaming', 'workstation')
            
        Returns:
            Image binary data (bytes) or None if failed
        """
        if not self.client:
            logger.warning("GenAI Client not initialized. Skipping generation.")
            return None

        try:
            # Construct prompt
            parts_summary = ", ".join([f"{c.get('category', 'Part')}: {c.get('name', 'Unknown')}" for c in components])
            
            prompt = (
                f"A high-quality, photorealistic 3D render of a custom built PC inside a modern case. "
                f"The PC is designed for {purpose}. "
                f"Visible components include: {parts_summary}. "
                f"The internal lighting matches a {purpose} theme (e.g. RGB for gaming, clean white/blue for workstation). "
                f"Show the internal layout clearly with glass side panel. "
                f"Clean background, studio lighting, 4k resolution, highly detailed."
            )
            
            logger.info(f"Generating image with prompt: {prompt[:100]}...")

            # Configuration
            model = "gemini-3-pro-image-preview" # User requested model
            
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                temperature=1,
                top_p=0.95,
                max_output_tokens=8192,
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    image_size="1024x1024", 
                ),
            )
            
            # Use generate_content instead of stream for single image
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=generate_content_config,
            )
            
            # Extract Image
            if (response.candidates 
                and response.candidates[0].content 
                and response.candidates[0].content.parts):
                
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                         return part.inline_data.data # This is bytes
            
            logger.error("No image data found in response.")
            return None

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None
