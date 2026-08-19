"""
Automated Test Suite for AI Tool-Calling Agent.
Tests all individual tools, edge cases, tool registry, and agent integration.
"""

import sys
import unittest
from typing import Dict, Any

from tools.calculator import calculate
from tools.weather import get_weather, geocode_location
from tools.text_utils import text_operations, count_words, reverse_text
from tools.currency import convert_currency
from tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS, execute_tool
from agent import AIAgent


class TestCalculatorTool(unittest.TestCase):
    """Tests for the Safe Calculator Tool."""

    def test_addition(self):
        res = calculate("125 + 450")
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 575)

    def test_multiplication(self):
        res = calculate("25 * 40")
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 1000)

    def test_percentage_of(self):
        res = calculate("15% of 800")
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 120)

    def test_percentage_alt(self):
        res = calculate("25% of 800")
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 200)

    def test_complex_expression(self):
        res = calculate("(10 + 5) * 3 - 5")
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 40)

    def test_division_by_zero(self):
        res = calculate("25 / 0")
        self.assertFalse(res["success"])
        self.assertIn("Division by zero", res["error"])

    def test_invalid_math_input(self):
        res = calculate("hello + 25")
        self.assertFalse(res["success"])
        self.assertIsNotNone(res["error"])

    def test_modulo_operator(self):
        res = calculate("100 % 12")
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 4)

    def test_percentage_of_twelve(self):
        res = calculate("100% of 12")
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 12)

    def test_empty_input(self):
        res = calculate("")
        self.assertFalse(res["success"])


class TestWeatherTool(unittest.TestCase):
    """Tests for the Open-Meteo Weather Tool."""

    def test_geocoding_valid_city(self):
        geo = geocode_location("Mumbai")
        self.assertIsNotNone(geo)
        self.assertEqual(geo["name"], "Mumbai")
        self.assertAlmostEqual(geo["latitude"], 19.07, places=1)

    def test_get_weather_valid_city(self):
        res = get_weather("Mumbai")
        self.assertTrue(res["success"])
        self.assertIn("Mumbai", res["location"])
        self.assertIsNotNone(res["temperature_c"])
        self.assertIsNotNone(res["condition"])

    def test_get_weather_delhi(self):
        res = get_weather("Delhi")
        self.assertTrue(res["success"])
        self.assertIn("Delhi", res["location"])
        self.assertIsNotNone(res["temperature_c"])

    def test_invalid_location(self):
        res = get_weather("NonExistentCityXYZ987654321")
        self.assertFalse(res["success"])
        self.assertIn("Could not find coordinates", res["error"])

    def test_empty_location(self):
        res = get_weather("")
        self.assertFalse(res["success"])


class TestTextUtilsTool(unittest.TestCase):
    """Tests for Word/Text Utility Tool."""

    def test_word_count(self):
        res = text_operations("Artificial intelligence is interesting", operation="word_count")
        self.assertTrue(res["success"])
        self.assertEqual(res["word_count"], 4)

    def test_reverse_text(self):
        res = text_operations("Hello World", operation="reverse")
        self.assertTrue(res["success"])
        self.assertEqual(res["reversed_text"], "dlroW olleH")

    def test_char_count(self):
        res = text_operations("Hello", operation="char_count")
        self.assertTrue(res["success"])
        self.assertEqual(res["char_count_total"], 5)

    def test_case_conversions(self):
        res_upper = text_operations("hello world", operation="uppercase")
        self.assertEqual(res_upper["result"], "HELLO WORLD")
        res_lower = text_operations("HELLO WORLD", operation="lowercase")
        self.assertEqual(res_lower["result"], "hello world")

    def test_empty_text(self):
        res = text_operations("", operation="reverse")
        self.assertTrue(res["success"])
        self.assertEqual(res["reversed_text"], "")
        self.assertEqual(res["word_count"], 0)


class TestCurrencyTool(unittest.TestCase):
    """Tests for Frankfurter Currency Converter Tool."""

    def test_usd_to_inr(self):
        res = convert_currency(100, "USD", "INR")
        self.assertTrue(res["success"])
        self.assertEqual(res["from_currency"], "USD")
        self.assertEqual(res["to_currency"], "INR")
        self.assertGreater(res["converted_amount"], 0)

    def test_same_currency(self):
        res = convert_currency(50, "USD", "USD")
        self.assertTrue(res["success"])
        self.assertEqual(res["converted_amount"], 50.0)

    def test_invalid_currency(self):
        res = convert_currency(100, "INVALID_XYZ", "INR")
        self.assertFalse(res["success"])
        self.assertIsNotNone(res["error"])

    def test_negative_amount(self):
        res = convert_currency(-50, "USD", "INR")
        self.assertFalse(res["success"])


class TestToolRegistry(unittest.TestCase):
    """Tests for Tool Registry and execution dispatcher."""

    def test_registered_tools_count(self):
        self.assertEqual(len(TOOL_DEFINITIONS), 4)
        names = {t["name"] for t in TOOL_DEFINITIONS}
        self.assertSetEqual(names, {"calculate", "get_weather", "text_operations", "convert_currency"})

    def test_execute_tool_calculator(self):
        res = execute_tool("calculate", {"expression": "50 * 2"})
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 100)

    def test_execute_unknown_tool(self):
        res = execute_tool("unknown_tool_xyz", {})
        self.assertFalse(res["success"])
        self.assertIn("not registered", res["error"])


class TestAgentBasic(unittest.TestCase):
    """Tests for AIAgent initialization and basic safety."""

    def test_agent_init(self):
        agent = AIAgent()
        self.assertIsNotNone(agent)

    def test_empty_prompt(self):
        agent = AIAgent()
        res = agent.run("")
        self.assertFalse(res["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
