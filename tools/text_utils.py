"""
Word/Text Utility Tool: Local text analysis and transformations.
Provides word count, character count, text reversal, case conversion, etc.
"""

from typing import Dict, Any, Optional


def text_operations(
    text: str,
    operation: str = "all"
) -> Dict[str, Any]:
    """
    Perform various text analysis and transformation operations.

    Args:
        text (str): The input text to analyze or manipulate.
        operation (str): The specific operation to perform:
            - 'word_count': Count words
            - 'reverse': Reverse the string
            - 'char_count': Count characters
            - 'uppercase': Convert to uppercase
            - 'lowercase': Convert to lowercase
            - 'all': Return comprehensive analysis and transformations

    Returns:
        Dict[str, Any]: Result containing counts, reversed text, and summary.
    """
    if text is None:
        text = ""

    # Strip and handle empty string
    stripped = text.strip()
    words = [w for w in stripped.split() if w] if stripped else []
    word_cnt = len(words)
    char_cnt_total = len(text)
    char_cnt_no_spaces = len(text.replace(" ", "").replace("\t", "").replace("\n", ""))
    reversed_str = text[::-1]

    op = (operation or "all").lower().strip()

    if op in ("word_count", "count_words", "words"):
        return {
            "success": True,
            "operation": "word_count",
            "input_text": text,
            "word_count": word_cnt,
            "char_count_total": char_cnt_total,
            "formatted": f"The text contains {word_cnt} word{'s' if word_cnt != 1 else ''}.",
            "error": None
        }

    elif op in ("reverse", "reverse_text"):
        return {
            "success": True,
            "operation": "reverse",
            "input_text": text,
            "reversed_text": reversed_str,
            "word_count": word_cnt,
            "char_count_total": char_cnt_total,
            "formatted": f"Reversed text: \"{reversed_str}\"",
            "error": None
        }

    elif op in ("char_count", "character_count"):
        return {
            "success": True,
            "operation": "char_count",
            "input_text": text,
            "char_count_total": char_cnt_total,
            "char_count_no_spaces": char_cnt_no_spaces,
            "formatted": f"The text has {char_cnt_total} characters ({char_cnt_no_spaces} excluding spaces).",
            "error": None
        }

    elif op in ("uppercase", "upper"):
        return {
            "success": True,
            "operation": "uppercase",
            "input_text": text,
            "result": text.upper(),
            "formatted": text.upper(),
            "error": None
        }

    elif op in ("lowercase", "lower"):
        return {
            "success": True,
            "operation": "lowercase",
            "input_text": text,
            "result": text.lower(),
            "formatted": text.lower(),
            "error": None
        }

    # Default 'all' or comprehensive mode
    return {
        "success": True,
        "operation": "all",
        "input_text": text,
        "word_count": word_cnt,
        "char_count_total": char_cnt_total,
        "char_count_no_spaces": char_cnt_no_spaces,
        "reversed_text": reversed_str,
        "uppercase": text.upper(),
        "lowercase": text.lower(),
        "formatted": (
            f"Text Analysis:\n"
            f"- Word count: {word_cnt}\n"
            f"- Character count: {char_cnt_total} (non-space: {char_cnt_no_spaces})\n"
            f"- Reversed: \"{reversed_str}\""
        ),
        "error": None
    }


def count_words(text: str) -> Dict[str, Any]:
    """Helper shortcut for word counting."""
    return text_operations(text, operation="word_count")


def reverse_text(text: str) -> Dict[str, Any]:
    """Helper shortcut for reversing text."""
    return text_operations(text, operation="reverse")


# Tool specification for LLM tool calling
TEXT_TOOL_DEFINITION = {
    "name": "text_operations",
    "description": "Performs text manipulation and analysis including word count, character count, text reversal, and case transformation. Use this whenever the user asks to count words, count letters/characters, reverse text, or transform string casing.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "text": {
                "type": "STRING",
                "description": "The target text to analyze or transform"
            },
            "operation": {
                "type": "STRING",
                "description": "Operation type: 'word_count' (to count words), 'reverse' (to reverse characters), 'char_count' (to count characters), or 'all' (comprehensive analysis)",
                "enum": ["word_count", "reverse", "char_count", "uppercase", "lowercase", "all"]
            }
        },
        "required": ["text"]
    }
}
