"""
OpenAI API client for gpt-4.1-mini text and vision analysis.

Provides structured interfaces for text parsing and vision analysis with
proper error handling and response validation.
"""

import json
import logging
from typing import Dict, Any, List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .base_client import BaseAPIClient, api_call
from ..exceptions import OpenAIError, ValidationError

logger = logging.getLogger(__name__)


class OpenAIClient(BaseAPIClient):
    """Client for OpenAI gpt-4.1-mini API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI client.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__('OpenAI', config)
        self.api_key = config.get('api_keys', {}).get('openai_api_key')
        
        if self.api_key and OpenAI:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def is_configured(self) -> bool:
        """Check if OpenAI client is properly configured."""
        return bool(self.api_key and OpenAI and self.client)
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        if not self.is_configured():
            return False
        
        try:
            # Simple test call
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return bool(response.choices)
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False
    
    @api_call
    def extract_website_tips(self, transcript: str) -> List[Dict[str, str]]:
        """Extract website tips from transcript using gpt-4.1-mini.
        
        Args:
            transcript: Video transcript text
            
        Returns:
            List of extracted website tips
            
        Raises:
            OpenAIError: If API call fails
            ValidationError: If response format is invalid
        """
        if not self.is_configured():
            raise OpenAIError("OpenAI client not configured")
        
        system_prompt = self._get_text_parsing_prompt()
        user_prompt = f"""Please analyze this YouTube video transcript and extract any website recommendations or tips:

TRANSCRIPT:
{transcript}

Extract the website tips as JSON:"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            return self._parse_tips_response(content)
            
        except Exception as e:
            raise OpenAIError(f"Failed to extract website tips: {str(e)}")

    @api_call
    def extract_website_info_with_context(self, transcript: str, website_url: str) -> Optional[Dict[str, str]]:
        """Extract specific website information from transcript with URL context.

        Args:
            transcript: Video transcript text
            website_url: Specific website URL to analyze

        Returns:
            Dictionary with 'use' and 'details' fields or None if failed

        Raises:
            OpenAIError: If API call fails
        """
        if not self.is_configured():
            raise OpenAIError("OpenAI client not configured")

        system_prompt = f"""You are an expert at analyzing YouTube video transcripts to extract detailed information about specific websites mentioned.

The speaker has mentioned the website: {website_url}

Your task is to analyze the transcript and extract:
1. What this specific website is used for (its purpose and functionality)
2. Additional details about why it's useful, how to use it, or specific features mentioned

IMPORTANT FORMATTING GUIDELINES:
- "use" field: CONCISE, single-sentence description (under 100 characters) of the main purpose
- "details" field: COMPREHENSIVE description with full functionality, benefits, and context from transcript
- Focus on what the speaker actually says about this website, not generic descriptions
- Extract specific information mentioned in the transcript

Return a JSON object with this structure:
{{
  "use": "Concise description of what the website does (under 100 characters)",
  "details": "Comprehensive description with functionality, benefits, and context from the transcript"
}}

If the website is not clearly described in the transcript, return null."""

        user_prompt = f"""Please analyze this transcript and extract information about {website_url}:

TRANSCRIPT:
{transcript}

Extract the website information as JSON:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()
            return self._parse_website_info_response(content)

        except Exception as e:
            raise OpenAIError(f"Failed to extract website info with context: {str(e)}")

    @api_call
    def extract_general_website_info(self, transcript: str) -> Optional[Dict[str, str]]:
        """Extract general website information from transcript when no specific URL is known.

        Args:
            transcript: Video transcript text

        Returns:
            Dictionary with 'use' and 'details' fields or None if failed

        Raises:
            OpenAIError: If API call fails
        """
        if not self.is_configured():
            raise OpenAIError("OpenAI client not configured")

        system_prompt = """You are an expert at analyzing YouTube video transcripts to extract information about websites, tools, or online services mentioned.

The speaker has mentioned a website or online tool but the specific URL was not visually identified. Your task is to analyze the transcript and extract:
1. What the website/tool is used for based on the context and description
2. Additional details about its functionality, benefits, or how to use it

Focus on what the speaker actually says about the website or tool. Provide meaningful, descriptive content based on the transcript.

Return a JSON object with this structure:
{
  "use": "Concise description of what the website/tool does (1 sentence, under 100 characters)",
  "details": "Comprehensive description with functionality, benefits, and context from the transcript"
}

If no clear website or tool information can be extracted, return null."""

        user_prompt = f"""Please analyze this transcript and extract information about any website, tool, or online service mentioned:

TRANSCRIPT:
{transcript}

Extract the website/tool information as JSON:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()
            return self._parse_website_info_response(content)

        except Exception as e:
            raise OpenAIError(f"Failed to extract general website info: {str(e)}")
    
    @api_call
    def analyze_frame_for_urls(self, image_data: str, expected_website: str) -> Optional[Dict[str, Any]]:
        """Analyze video frame for URLs using gpt-4.1-mini vision.
        
        Args:
            image_data: Base64-encoded image data
            expected_website: Expected website name to look for
            
        Returns:
            Analysis result with confidence score or None
            
        Raises:
            OpenAIError: If API call fails
        """
        if not self.is_configured():
            raise OpenAIError("OpenAI client not configured")
        
        system_prompt = self._get_vision_analysis_prompt(expected_website)
        user_prompt = f"Analyze this video frame and look for any URLs or text related to '{expected_website}'. Focus on any visible website addresses, domain names, or related text."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            return self._parse_vision_response(content)
            
        except Exception as e:
            raise OpenAIError(f"Failed to analyze frame: {str(e)}")
    
    def _get_text_parsing_prompt(self) -> str:
        """Get system prompt for text parsing."""
        return """You are an expert at analyzing YouTube video transcripts to extract website recommendations and tips.

Your task is to identify when the speaker mentions specific websites, tools, or online services and extract detailed information about them.

For each website/tool mentioned, extract:
1. The website/tool name (domain or service name)
2. What it's used for - A CONCISE, single-sentence description (under 100 characters) of the tool's main purpose
3. Additional details - A COMPREHENSIVE description with functionality, benefits, features, and context from the transcript

IMPORTANT FORMATTING GUIDELINES:
- "use" field: Keep it concise and focused (1 sentence, under 100 characters)
- "details" field: Provide comprehensive information with full context from what the speaker says
- Focus on what the speaker actually says about each tool, not generic descriptions
- Extract meaningful, specific information based on the transcript content

Focus on providing meaningful, descriptive content for the "use" and "details" fields based on what the speaker actually says about each tool.

Examples of good extraction:
- "use": "Interactive historical timeline that shows world events and civilizations across different time periods"
- "details": "Allows you to explore history visually by zooming in and out of different eras and geographical regions"

Return your findings as a JSON array of objects with this structure:
[
  {
    "website": "example.com",
    "use": "Clear description of what the tool does and its main purpose",
    "details": "Additional context, features, benefits, or usage instructions mentioned by the speaker"
  }
]

If no websites or tools are mentioned, return an empty array [].

Rules:
- Only include actual websites, tools, or online services mentioned
- Be specific about the website name (include .com, .org, etc. if mentioned)
- Keep descriptions concise but informative
- If no websites are mentioned, return an empty array []
- Focus on actionable recommendations, not just casual mentions"""
    
    def _get_vision_analysis_prompt(self, website: str) -> str:
        """Get system prompt for vision analysis."""
        return f"""You are an expert at analyzing video frames to detect website URLs and text.

Look for any visible URLs, website names, or text that matches or relates to: {website}

Return a JSON object with:
{{
  "url_detected": true/false,
  "detected_text": "any URLs or website text you can see",
  "confidence": 0-100 (how confident you are that this frame shows the website),
  "description": "brief description of what you see"
}}"""
    
    def _parse_tips_response(self, content: str) -> List[Dict[str, str]]:
        """Parse GPT response for website tips.
        
        Args:
            content: Raw GPT response content
            
        Returns:
            List of validated tips
            
        Raises:
            ValidationError: If response format is invalid
        """
        try:
            # Extract JSON from response
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start < 0 or json_end <= json_start:
                logger.warning("No valid JSON array found in GPT response")
                return []
            
            json_content = content[json_start:json_end]
            tips = json.loads(json_content)
            
            if not isinstance(tips, list):
                raise ValidationError("GPT response is not a list")
            
            # Validate and clean tips
            validated_tips = []
            for tip in tips:
                if isinstance(tip, dict) and 'website' in tip:
                    validated_tips.append({
                        'website': str(tip.get('website', '')),
                        'use': str(tip.get('use', '')),
                        'details': str(tip.get('details', '')),
                        'frame_path': ''  # Will be filled in vision phase
                    })
            
            logger.debug(f"Extracted {len(validated_tips)} tips from transcript")
            return validated_tips
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"Failed to parse GPT JSON response: {e}")
        except Exception as e:
            raise ValidationError(f"Invalid GPT response format: {e}")
    
    def _parse_vision_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse GPT vision response.
        
        Args:
            content: Raw GPT response content
            
        Returns:
            Parsed vision analysis result or None
        """
        try:
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start < 0 or json_end <= json_start:
                logger.warning("No valid JSON found in GPT vision response")
                return None
            
            json_content = content[json_start:json_end]
            result = json.loads(json_content)
            
            # Validate required fields
            if not isinstance(result, dict):
                return None
            
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse GPT vision JSON response: {e}")
            return None
        except Exception as e:
            logger.warning(f"Invalid GPT vision response format: {e}")
            return None

    def _parse_website_info_response(self, content: str) -> Optional[Dict[str, str]]:
        """Parse website info response from GPT.

        Args:
            content: GPT response content

        Returns:
            Parsed website info or None if failed
        """
        try:
            # Handle null response
            if content.lower().strip() in ['null', 'none', '{}']:
                return None

            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

            if json_start < 0 or json_end <= json_start:
                logger.warning("No valid JSON object found in website info response")
                return None

            json_content = content[json_start:json_end]
            website_info = json.loads(json_content)

            if not isinstance(website_info, dict):
                logger.warning("Website info response is not a dictionary")
                return None

            # Validate and clean website info
            if 'use' in website_info and 'details' in website_info:
                return {
                    'use': str(website_info.get('use', '')).strip(),
                    'details': str(website_info.get('details', '')).strip()
                }
            else:
                logger.warning("Website info response missing required fields")
                return None

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse website info response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing website info response: {e}")
            return None
