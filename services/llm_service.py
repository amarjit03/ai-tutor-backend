"""
LLM Service - Groq API integration
"""
import json
import re
from typing import Optional, Dict, Any
from groq import Groq

from config import settings


class LLMService:
    """Handles all LLM interactions via Groq API"""
    
    def __init__(self):
        self.client = None
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
    
    def _get_client(self) -> Groq:
        """Get or create Groq client"""
        if self.client is None:
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not set in environment")
            self.client = Groq(api_key=settings.GROQ_API_KEY)
        return self.client
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response"""
        # Try to find JSON block in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find raw JSON object
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Try parsing the entire text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        return None
    
    async def generate(
        self,
        prompt: str,
        user_message: Optional[str] = None,
        expect_json: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM
        
        Args:
            prompt: System prompt with instructions
            user_message: Optional user message to respond to
            expect_json: Whether to parse response as JSON
            temperature: Override default temperature
            max_tokens: Override default max tokens
        
        Returns:
            Dict with 'success', 'response' (parsed JSON or text), and 'raw_response'
        """
        try:
            client = self._get_client()
            
            messages = [{"role": "system", "content": prompt}]
            
            if user_message:
                messages.append({"role": "user", "content": user_message})
            else:
                # If no user message, add a simple prompt to get started
                messages.append({"role": "user", "content": "Please proceed."})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            
            raw_response = response.choices[0].message.content
            
            if expect_json:
                parsed = self._extract_json(raw_response)
                if parsed:
                    return {
                        "success": True,
                        "response": parsed,
                        "raw_response": raw_response
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to parse JSON from response",
                        "raw_response": raw_response
                    }
            else:
                return {
                    "success": True,
                    "response": raw_response,
                    "raw_response": raw_response
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_response": None
            }
    
    def generate_sync(
        self,
        prompt: str,
        user_message: Optional[str] = None,
        expect_json: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of generate
        """
        try:
            client = self._get_client()
            
            messages = [{"role": "system", "content": prompt}]
            
            if user_message:
                messages.append({"role": "user", "content": user_message})
            else:
                messages.append({"role": "user", "content": "Please proceed."})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            
            raw_response = response.choices[0].message.content
            
            if expect_json:
                parsed = self._extract_json(raw_response)
                if parsed:
                    return {
                        "success": True,
                        "response": parsed,
                        "raw_response": raw_response
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to parse JSON from response",
                        "raw_response": raw_response
                    }
            else:
                return {
                    "success": True,
                    "response": raw_response,
                    "raw_response": raw_response
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_response": None
            }
    
    async def generate_with_history(
        self,
        system_prompt: str,
        conversation_history: list,
        user_message: str,
        expect_json: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response with conversation history
        
        Args:
            system_prompt: System instructions
            conversation_history: List of {"role": "user/assistant", "content": "..."}
            user_message: Current user message
            expect_json: Whether to parse as JSON
        """
        try:
            client = self._get_client()
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": user_message})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            raw_response = response.choices[0].message.content
            
            if expect_json:
                parsed = self._extract_json(raw_response)
                if parsed:
                    return {
                        "success": True,
                        "response": parsed,
                        "raw_response": raw_response
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to parse JSON",
                        "raw_response": raw_response
                    }
            
            return {
                "success": True,
                "response": raw_response,
                "raw_response": raw_response
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw_response": None
            }


# Singleton instance
llm_service = LLMService()
