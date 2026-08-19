"""
Calculator Tool: Safe evaluation of mathematical expressions and percentages.
"""

import ast
import operator
import math
import re
from typing import Dict, Any, Union


# Supported mathematical operators for safe AST evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "log": math.log10,
    "ln": math.log,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval_node(node: ast.AST) -> Union[int, float]:
    """Recursively evaluate an AST node safely."""
    if isinstance(node, ast.Constant):  # Numbers
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    elif isinstance(node, ast.BinOp):  # Binary operations (e.g., a + b)
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ZeroDivisionError("Division by zero is undefined.")
        return SAFE_OPERATORS[op_type](left, right)

    elif isinstance(node, ast.UnaryOp):  # Unary operations (e.g., -a)
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _safe_eval_node(node.operand)
        return SAFE_OPERATORS[op_type](operand)

    elif isinstance(node, ast.Call):  # Allowed math functions
        if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCTIONS:
            func = SAFE_FUNCTIONS[node.func.id]
            args = [_safe_eval_node(arg) for arg in node.args]
            return func(*args)
        raise ValueError(f"Function call not permitted: {ast.dump(node)}")

    elif isinstance(node, ast.Name):  # Constants like pi, e
        if node.id in SAFE_FUNCTIONS:
            return SAFE_FUNCTIONS[node.id]
        raise ValueError(f"Variable '{node.id}' is not defined.")

    else:
        raise ValueError(f"Unsupported syntax in expression: {type(node).__name__}")


def preprocess_expression(expr: str) -> str:
    """
    Clean and preprocess natural language math patterns.
    Examples:
      - '15% of 800' -> '(15 / 100) * 800'
      - '25%' -> '(25 / 100)'
      - 'x' or 'X' or '×' -> '*'
      - '÷' -> '/'
      - '^' -> '**'
    """
    cleaned = expr.strip()

    # Replace unicode multiplication/division symbols
    cleaned = cleaned.replace("×", "*").replace("÷", "/")

    # Handle percentage pattern: 'X% of Y' or 'X % of Y' (strictly requiring 'of')
    percent_of_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%\s*of\s+(\d+(?:\.\d+)?)', re.IGNORECASE)
    while percent_of_pattern.search(cleaned):
        cleaned = percent_of_pattern.sub(r'(\1 / 100) * \2', cleaned)

    # Handle trailing percentage: 'X%' NOT followed by another operand (to avoid breaking modulo like '100 % 12')
    percent_trailing_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%(?!\s*(?:of\s+)?\d)')
    cleaned = percent_trailing_pattern.sub(r'(\1 / 100)', cleaned)

    # Replace caret ^ with power **
    cleaned = cleaned.replace("^", "**")

    # Replace 'x' between numbers or parentheses as multiplication (e.g., '25 x 40')
    cleaned = re.sub(r'(\d+)\s*[xX]\s*(\d+)', r'\1 * \2', cleaned)

    return cleaned


def calculate(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate a mathematical expression or percentage.

    Args:
        expression (str): The mathematical expression to evaluate (e.g., "25 * 40", "15% of 800", "125 + 450").

    Returns:
        Dict[str, Any]: {
            "success": bool,
            "expression": str,
            "result": Union[int, float, str],
            "formatted": str,
            "error": Optional[str]
        }
    """
    if not expression or not expression.strip():
        return {
            "success": False,
            "expression": expression,
            "result": None,
            "formatted": "",
            "error": "Expression is empty. Please provide a mathematical expression."
        }

    raw_expr = expression.strip()
    try:
        processed_expr = preprocess_expression(raw_expr)
        parsed_tree = ast.parse(processed_expr, mode="eval")
        result = _safe_eval_node(parsed_tree.body)

        # Format integer results without unnecessary decimal zeros (e.g., 1000 instead of 1000.0)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        elif isinstance(result, float):
            result = round(result, 6)

        return {
            "success": True,
            "expression": raw_expr,
            "result": result,
            "formatted": f"{raw_expr} = {result}",
            "error": None
        }

    except ZeroDivisionError:
        return {
            "success": False,
            "expression": raw_expr,
            "result": None,
            "formatted": "",
            "error": "Division by zero is undefined."
        }
    except (SyntaxError, ValueError) as e:
        return {
            "success": False,
            "expression": raw_expr,
            "result": None,
            "formatted": "",
            "error": f"Invalid mathematical expression: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "expression": raw_expr,
            "result": None,
            "formatted": "",
            "error": f"Calculation error: {str(e)}"
        }


# Tool specification for LLM tool calling
CALCULATOR_TOOL_DEFINITION = {
    "name": "calculate",
    "description": "Performs mathematical calculations including arithmetic (+, -, *, /, ^), percentages (e.g. '15% of 800'), powers, and standard math operations. Use this tool whenever a math calculation is needed.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "expression": {
                "type": "STRING",
                "description": "The mathematical expression to evaluate, e.g., '25 * 40', '15% of 800', '125 + 450', or 'sqrt(144)'"
            }
        },
        "required": ["expression"]
    }
}
