import requests
import json
import time
from typing import Optional

class LLMRefiner:
    """Text refinement using Ollama LLM models for natural dubbing"""
    
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.session = requests.Session()
    
    def refine_text(self, original: str, translated: str, duration: float, emotion: Optional[str] = None) -> str:
        """
        Refine translated text to sound more natural and fit duration
        
        Args:
            original: Original text in source language
            translated: Raw translated text
            duration: Available duration in seconds
            emotion: Target emotion (optional)
            
        Returns:
            Refined text that sounds more natural
        """
        prompt = self._create_refinement_prompt(original, translated, duration, emotion)
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for consistency
                        "top_p": 0.9,
                        "max_tokens": 100
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                refined = result.get("response", "").strip()
                
                # Validate response
                if refined and len(refined) > 0:
                    return refined
                else:
                    print(f"⚠️ LLM returned empty response, using original translation")
                    return translated
                    
            else:
                print(f"⚠️ LLM request failed with status {response.status_code}")
                return translated
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ LLM connection error: {e}")
            return translated
        except json.JSONDecodeError as e:
            print(f"⚠️ LLM response parsing error: {e}")
            return translated
        except Exception as e:
            print(f"⚠️ LLM refinement error: {e}")
            return translated
    
    def _create_refinement_prompt(self, original: str, translated: str, duration: float, emotion: Optional[str]) -> str:
        """Create prompt for text refinement"""
        
        base_prompt = f"""You are an expert movie dubbing assistant. Your task is to refine translated dialogue to sound natural and fit the timing constraints.

ORIGINAL TEXT:
{original}

TRANSLATED TEXT:
{translated}

AVAILABLE DURATION: {duration:.2f} seconds

REQUIREMENTS:
- Make the dialogue sound natural and conversational
- Ensure it can be spoken within {duration:.2f} seconds
- Preserve the original meaning and intent
- Match the emotional tone of the scene
"""

        if emotion:
            base_prompt += f"""
- Add {emotion} emotional tone to the dialogue
"""

        base_prompt += """

RESPONSE FORMAT:
Provide only the refined dialogue, nothing else. No explanations or alternatives.

REFINED DIALOGUE:"""

        return base_prompt
    
    def batch_refine(self, lines: list, batch_size: int = 3) -> list:
        """
        Refine multiple lines efficiently by batching
        
        Args:
            lines: List of dictionaries with 'original', 'translated', 'duration', 'emotion' keys
            batch_size: Number of lines to process in each batch
            
        Returns:
            List of refined texts
        """
        refined_texts = []
        
        for i in range(0, len(lines), batch_size):
            batch = lines[i:i + batch_size]
            batch_results = []
            
            for line in batch:
                # Smart heuristic: only refine longer or complex lines
                if self._should_refine(line):
                    refined = self.refine_text(
                        original=line['original'],
                        translated=line['translated'],
                        duration=line['duration'],
                        emotion=line.get('emotion')
                    )
                    batch_results.append(refined)
                    
                    # Small delay to avoid overwhelming Ollama
                    time.sleep(0.5)
                else:
                    # Use original translation for simple lines
                    batch_results.append(line['translated'])
            
            refined_texts.extend(batch_results)
            
            # Progress indicator
            progress = min((i + batch_size) / len(lines) * 100, 100)
            print(f"🧠 LLM Refinement: {progress:.1f}% complete")
        
        return refined_texts
    
    def _should_refine(self, line: dict) -> bool:
        """
        Smart heuristic to decide if a line needs LLM refinement
        
        Args:
            line: Dictionary with translation info
            
        Returns:
            True if line should be refined, False otherwise
        """
        translated = line['translated']
        duration = line['duration']
        
        # Refine if:
        # 1. Line is long (more than 8 words)
        # 2. Duration is long enough to support refinement (> 2 seconds)
        # 3. Contains complex punctuation or structure
        
        word_count = len(translated.split())
        
        # Check word count
        if word_count > 8:
            return True
        
        # Check duration
        if duration > 2.0:
            return True
        
        # Check for complexity indicators
        complex_indicators = ['?', '!', ';', ':', '...', '"', "'"]
        if any(indicator in translated for indicator in complex_indicators):
            return True
        
        # Check for very short lines (probably don't need refinement)
        if word_count <= 3 and duration < 1.0:
            return False
        
        # Default to refine for medium complexity
        return word_count >= 4
    
    def detect_emotion(self, text: str) -> str:
        """
        Simple emotion detection based on text patterns
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected emotion as string
        """
        text_lower = text.lower()
        
        # Emotion keywords
        emotion_patterns = {
            'angry': ['!', 'damn', 'hell', 'bastard', 'shut up', 'get out'],
            'sad': ['...', 'cry', 'tears', 'goodbye', 'sorry', 'miss'],
            'happy': ['!', 'great', 'wonderful', 'love', 'yes', 'thank'],
            'surprised': ['what', 'how', 'when', 'why', 'really', 'no way'],
            'fear': ['help', 'scared', 'afraid', 'run', 'danger', 'please'],
            'neutral': []  # Default
        }
        
        for emotion, keywords in emotion_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        
        return 'neutral'
    
    def test_connection(self) -> bool:
        """Test if Ollama is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

# Global refiner instance
_refiner = None

def get_refiner(model: str = "llama3") -> LLMRefiner:
    """Get or create LLM refiner instance"""
    global _refiner
    if _refiner is None:
        _refiner = LLMRefiner(model=model)
        if not _refiner.test_connection():
            print("⚠️ Ollama not accessible. Using original translations without refinement.")
        else:
            print(f"🧠 LLM Refiner initialized with {model} model")
    return _refiner

def refine_translated_text(original: str, translated: str, duration: float, emotion: Optional[str] = None, model: str = "llama3") -> str:
    """
    Convenience function to refine translated text
    
    Args:
        original: Original text
        translated: Translated text
        duration: Available duration
        emotion: Target emotion (optional)
        model: LLM model to use
        
    Returns:
        Refined text
    """
    refiner = get_refiner(model)
    return refiner.refine_text(original, translated, duration, emotion)
