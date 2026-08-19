"""
AIAgent: Production-Ready MVP Tool-Calling Agent.
Implements: User -> LLM Agent -> Tool Selection -> Tool Execution -> Tool Result -> LLM -> Final Response.
"""

import os
import sys
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
import requests
from dotenv import load_dotenv

from tools import TOOL_FUNCTIONS, TOOL_DEFINITIONS, execute_tool

# Configure Windows terminal stdout encoding
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load environment variables
load_dotenv()

# Logger setup
logger = logging.getLogger("AIAgent")


class AIAgent:
    """
    Intelligent Tool-Calling Agent using Google Gemini API.
    Supports both live Gemini LLM function-calling and a local Mock/Development mode
    to test tool calling and pipelines without consuming API quota.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3.6-flash", mock_mode: Optional[bool] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", model)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.history: List[Dict[str, Any]] = []

        # Determine mock/development mode from param or env
        env_mock = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")
        self.mock_mode = mock_mode if mock_mode is not None else env_mock

        self.system_instruction = (
            "You are a helpful, capable, and accurate AI assistant. "
            "You have access to specialized tools for mathematical calculations, weather forecasts, "
            "text manipulation/word counting, and currency conversions. "
            "When the user's request requires any of these capabilities, use the appropriate tool. "
            "Do not make up facts or do complex arithmetic manually if a tool can do it. "
            "Once you receive the tool's result, respond to the user in a natural, polite, and helpful manner."
        )

        if self.mock_mode:
            logger.info("AIAgent running in LOCAL MOCK / DEVELOPMENT MODE (Zero API quota consumed).")
        elif not self.is_configured():
            logger.warning(
                "GEMINI_API_KEY is not configured in .env. Live LLM calls will require an API key."
            )

    def is_configured(self) -> bool:
        """Check if a valid Gemini API key is configured."""
        return bool(self.api_key and self.api_key.strip() not in ("", "your_gemini_api_key_here"))

    def reset_conversation(self) -> None:
        """Reset conversation history."""
        self.history = []

    def _call_gemini_api(self, contents: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, max_retries: int = 2) -> Tuple[bool, Any]:
        """
        Send a generateContent request to the Gemini REST API with retry handling for rate limits.
        """
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload: Dict[str, Any] = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": self.system_instruction}]
            }
        }

        if tools:
            payload["tools"] = [{"function_declarations": tools}]

        for attempt in range(max_retries + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    return True, response.json()

                if response.status_code == 429 and attempt < max_retries:
                    wait_time = 4 * (attempt + 1)
                    logger.warning(f"Rate limited (429). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    import time
                    time.sleep(wait_time)
                    continue

                err_msg = response.text
                try:
                    err_json = response.json()
                    err_msg = err_json.get("error", {}).get("message", response.text)
                except Exception:
                    pass

                if response.status_code == 429:
                    return False, "Rate limit reached for free tier. Please wait a few seconds and try again."

                logger.error(f"Gemini API Error ({response.status_code}): {err_msg}")
                return False, f"Gemini API Error ({response.status_code}): {err_msg}"

            except requests.exceptions.Timeout:
                logger.error("Gemini API request timed out.")
                return False, "Error: Request to Gemini API timed out. Please try again."
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error communicating with Gemini: {e}")
                return False, f"Network error: Unable to connect to Gemini API ({str(e)})."
            except Exception as e:
                logger.error(f"Unexpected error in _call_gemini_api: {e}")
                return False, f"An unexpected error occurred: {str(e)}"

        return False, "Failed after multiple retry attempts."

    def _mock_tool_decision(self, user_input: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[str]]:
        """
        Simulate LLM tool selection locally without calling external LLM API.
        Used for development and testing to conserve API quota.
        """
        import re
        text = user_input.strip()

        # 1. Currency Conversion
        # e.g., 'Convert 100 USD to INR', '50 EUR to USD'
        curr_match = re.search(r'(?:convert|change|how much is)?\s*(\d+(?:\.\d+)?)\s*([A-Za-z]{3}|\$|€|₹|£|USD|EUR|INR|GBP|JPY)\s*(?:to|in|into)\s*([A-Za-z]{3}|\$|€|₹|£|USD|EUR|INR|GBP|JPY)', text, re.IGNORECASE)
        if curr_match:
            amount = float(curr_match.group(1))
            from_curr = curr_match.group(2)
            to_curr = curr_match.group(3)
            return "convert_currency", {"amount": amount, "from_currency": from_curr, "to_currency": to_curr}, None

        # 2. Weather Lookup
        # e.g., 'weather in Mumbai', 'temperature in Delhi', 'weather for London'
        weather_match = re.search(r'(?:weather|temperature|forecast|temp)(?:\s+in|\s+for|\s+at)?\s+([A-Za-z\s]+?)(?:\?|\.|$)', text, re.IGNORECASE)
        if weather_match:
            raw_loc = weather_match.group(1).strip()
            # Clean common filler words
            cleaned_loc = re.sub(r'^(the\s+|current\s+|today\s+)', '', raw_loc, flags=re.IGNORECASE).strip()
            if cleaned_loc:
                return "get_weather", {"location": cleaned_loc}, None

        # 3. Text Utility - Reverse
        # e.g., 'reverse "Hello World"', 'reverse the text: Hello'
        if "reverse" in text.lower():
            # Extract quoted string or text after reverse
            quote_match = re.search(r'["\'](.*?)["\']', text)
            if quote_match:
                target_str = quote_match.group(1)
            else:
                target_str = re.sub(r'.*?reverse(?:\s+the\s+text)?(?:\s*:\s*|\s+)', '', text, flags=re.IGNORECASE).strip()
            return "text_operations", {"text": target_str, "operation": "reverse"}, None

        # 4. Text Utility - Word / Character Count
        # e.g., 'count the words in "..."', 'how many words'
        if any(k in text.lower() for k in ["count words", "word count", "how many words", "count the words", "count characters", "char count"]):
            quote_match = re.search(r'["\'](.*?)["\']', text)
            if quote_match:
                target_str = quote_match.group(1)
            else:
                target_str = re.sub(r'.*?(?:in|of)\s*[:\s]*', '', text, flags=re.IGNORECASE).strip()
            op = "char_count" if "char" in text.lower() else "word_count"
            return "text_operations", {"text": target_str, "operation": op}, None

        # 5. Calculator
        # e.g., '25 * 40', '15% of 800', '125 + 450', 'what is 25 / 0', 'sqrt(144)'
        math_match = re.search(r'(?:what is|calculate|compute|solve)?\s*([\d\.\s\+\-\*\/\^\%\(\)\×\÷xX]+(?:%\s*of\s*\d+)?|sqrt\(\d+\))(?:\?|\.|$)', text, re.IGNORECASE)
        # Check if the extracted text actually contains mathematical symbols or digits
        if math_match:
            expr_candidate = math_match.group(1).strip()
            if any(c in expr_candidate for c in ["+", "-", "*", "/", "%", "×", "÷", "^", "sqrt"]) and any(c.isdigit() for c in expr_candidate):
                return "calculate", {"expression": expr_candidate}, None

        # 6. Conversational response (No tool needed)
        if any(w in text.lower() for w in ["hello", "hi", "hey", "who are you", "what can you do", "help"]):
            return None, None, "Hello! I am your AI Tool-Calling Assistant. I can perform calculations, check real-time weather, analyze text/count words, and convert international currencies."

        return None, None, f"I understood your query: \"{text}\". In live mode, Gemini LLM handles open-ended questions. Use math, weather, text, or currency requests to test tools!"

    def run(self, user_input: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Process a user's natural language input:
        1. Send input with tool declarations to LLM (or mock decision engine in Dev Mode).
        2. If tool is chosen, execute it.
        3. Send tool result back to LLM (or synthesize locally).
        4. Return the final natural language response and execution metadata.
        """
        if not user_input or not user_input.strip():
            return {
                "response": "Please enter a question or request.",
                "tool_called": None,
                "tool_args": None,
                "tool_result": None,
                "success": False
            }

        cleaned_input = user_input.strip()

        # ==========================================================
        # LOCAL DEVELOPMENT / MOCK MODE (Zero API quota consumed)
        # ==========================================================
        if self.mock_mode:
            tool_name, tool_args, direct_resp = self._mock_tool_decision(cleaned_input)

            if not tool_name:
                return {
                    "response": direct_resp or "I processed your request in Development Mode.",
                    "tool_called": None,
                    "tool_args": None,
                    "tool_result": None,
                    "is_mock": True,
                    "success": True
                }

            if verbose:
                logger.info(f"[Dev Mode] Tool Selection: '{tool_name}' with args: {tool_args}")

            # Execute real tool locally
            tool_output = execute_tool(tool_name, tool_args)

            if verbose:
                logger.info(f"[Dev Mode] Tool Result: {tool_output}")

            final_text = tool_output.get("formatted") or str(tool_output.get("result") or tool_output)
            if not tool_output.get("success"):
                final_text = f"Error: {tool_output.get('error', 'Operation failed')}"

            return {
                "response": final_text,
                "tool_called": tool_name,
                "tool_args": tool_args,
                "tool_result": tool_output,
                "is_mock": True,
                "success": True
            }

        # ==========================================================
        # LIVE GEMINI LLM MODE
        # ==========================================================
        if not self.is_configured():
            return {
                "response": (
                    "[Notice] GEMINI_API_KEY is not configured.\n"
                    "Please add your Gemini API key to the .env file:\n"
                    "GEMINI_API_KEY=your_actual_key_here\n\n"
                    "Or set MOCK_MODE=true in .env to test without an API key!"
                ),
                "tool_called": None,
                "tool_args": None,
                "tool_result": None,
                "success": False
            }

        # Build message history for the current turn
        turn_contents = list(self.history)
        turn_contents.append({
            "role": "user",
            "parts": [{"text": cleaned_input}]
        })

        if verbose:
            logger.info(f"User Prompt: '{cleaned_input}'")

        # Step 1: Send user message with available tool definitions to Gemini
        success, result_data = self._call_gemini_api(turn_contents, tools=TOOL_DEFINITIONS)
        if not success:
            return {
                "response": str(result_data),
                "tool_called": None,
                "tool_args": None,
                "tool_result": None,
                "success": False
            }

        # Parse Gemini response
        candidates = result_data.get("candidates", [])
        if not candidates:
            return {
                "response": "No response received from the model.",
                "tool_called": None,
                "tool_args": None,
                "tool_result": None,
                "success": False
            }

        model_content = candidates[0].get("content", {})
        parts = model_content.get("parts", [])

        # Check if the model requested a tool execution (functionCall)
        function_call = None
        for part in parts:
            if "functionCall" in part:
                function_call = part["functionCall"]
                break

        # Case A: No tool needed (Standard conversational response)
        if not function_call:
            text_parts = [p.get("text", "") for p in parts if "text" in p]
            final_text = "".join(text_parts).strip() or "I'm not sure how to answer that."

            # Update conversation history
            self.history.append({"role": "user", "parts": [{"text": cleaned_input}]})
            self.history.append({"role": "model", "parts": [{"text": final_text}]})

            return {
                "response": final_text,
                "tool_called": None,
                "tool_args": None,
                "tool_result": None,
                "success": True
            }

        # Case B: Tool requested by LLM
        tool_name = function_call.get("name")
        tool_args = function_call.get("args", {})

        if verbose:
            logger.info(f"LLM Tool Selection: '{tool_name}' with args: {tool_args}")

        # Step 2: Execute the tool locally
        tool_output = execute_tool(tool_name, tool_args)

        if verbose:
            logger.info(f"Tool Result: {tool_output}")

        # Step 3: Send tool result back to Gemini for final natural language synthesis
        # Append exact model content returned by Gemini (preserves thought_signature)
        turn_contents.append(model_content)

        # Append user functionResponse turn
        turn_contents.append({
            "role": "user",
            "parts": [{
                "functionResponse": {
                    "name": tool_name,
                    "response": tool_output
                }
            }]
        })

        # Step 4: Get final natural language response from Gemini
        synth_success, synth_data = self._call_gemini_api(turn_contents, tools=TOOL_DEFINITIONS, max_retries=1)
        if not synth_success:
            # Fallback seamlessly to tool formatted output if LLM synthesis turn is rate-limited
            formatted_res = tool_output.get("formatted") or str(tool_output.get("result") or tool_output)
            final_response = f"{formatted_res}"
            if "Rate limit" in str(synth_data):
                final_response += " *(Note: Generated directly from tool output due to free-tier rate limit)*"

            self.history.append({"role": "user", "parts": [{"text": cleaned_input}]})
            self.history.append({"role": "model", "parts": [{"text": final_response}]})

            return {
                "response": final_response,
                "tool_called": tool_name,
                "tool_args": tool_args,
                "tool_result": tool_output,
                "success": True
            }

        synth_candidates = synth_data.get("candidates", [])
        if synth_candidates:
            synth_parts = synth_candidates[0].get("content", {}).get("parts", [])
            final_text_parts = [p.get("text", "") for p in synth_parts if "text" in p]
            final_response = "".join(final_text_parts).strip()
        else:
            final_response = tool_output.get("formatted") or str(tool_output)

        # Update history with full exchange
        self.history.append({"role": "user", "parts": [{"text": cleaned_input}]})
        self.history.append({"role": "model", "parts": [{"text": final_response}]})

        return {
            "response": final_response,
            "tool_called": tool_name,
            "tool_args": tool_args,
            "tool_result": tool_output,
            "success": True
        }
