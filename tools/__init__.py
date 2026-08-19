"""
Tools Package & Registry: Centralized registry for all agent tools.
"""

from typing import Dict, Any, Callable, List
import logging

from tools.calculator import calculate, CALCULATOR_TOOL_DEFINITION
from tools.weather import get_weather, WEATHER_TOOL_DEFINITION
from tools.text_utils import text_operations, TEXT_TOOL_DEFINITION
from tools.currency import convert_currency, CURRENCY_TOOL_DEFINITION

logger = logging.getLogger("ToolRegistry")

# Map of tool names to their corresponding callable Python functions
TOOL_FUNCTIONS: Dict[str, Callable] = {
    "calculate": calculate,
    "get_weather": get_weather,
    "text_operations": text_operations,
    "convert_currency": convert_currency,
}

# List of Gemini tool declarations
TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    CALCULATOR_TOOL_DEFINITION,
    WEATHER_TOOL_DEFINITION,
    TEXT_TOOL_DEFINITION,
    CURRENCY_TOOL_DEFINITION,
]


def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely execute a tool by its registered name with provided arguments.

    Args:
        name (str): Name of the tool (e.g. 'calculate', 'get_weather', etc.)
        arguments (Dict[str, Any]): Dictionary of arguments to pass to the tool.

    Returns:
        Dict[str, Any]: Result dictionary from the tool or error details.
    """
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        logger.error(f"Tool '{name}' not found in registry.")
        return {
            "success": False,
            "error": f"Tool '{name}' is not registered or supported.",
            "data": None
        }

    try:
        logger.info(f"Executing tool '{name}' with arguments: {arguments}")
        result = func(**arguments)
        logger.info(f"Tool '{name}' executed successfully.")
        return result
    except TypeError as te:
        logger.error(f"Argument mismatch for tool '{name}': {te}")
        return {
            "success": False,
            "error": f"Invalid arguments for tool '{name}': {str(te)}",
            "data": None
        }
    except Exception as e:
        logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Error executing tool '{name}': {str(e)}",
            "data": None
        }
