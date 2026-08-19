"""
Currency Converter Tool: Real-time currency exchange rates using the Frankfurter API.
No API key required.
"""

import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger("CurrencyTool")

# Common currency aliases and symbols mapping
CURRENCY_ALIASES = {
    "$": "USD",
    "DOLLAR": "USD",
    "DOLLARS": "USD",
    "US DOLLAR": "USD",
    "US DOLLARS": "USD",
    "USD": "USD",
    "€": "EUR",
    "EURO": "EUR",
    "EUROS": "EUR",
    "EUR": "EUR",
    "₹": "INR",
    "RUPEE": "INR",
    "RUPEES": "INR",
    "INR": "INR",
    "£": "GBP",
    "POUND": "GBP",
    "POUNDS": "GBP",
    "STERLING": "GBP",
    "GBP": "GBP",
    "¥": "JPY",
    "YEN": "JPY",
    "JPY": "JPY",
    "AUD": "AUD",
    "CAD": "CAD",
    "CHF": "CHF",
    "CNY": "CNY",
    "SGD": "SGD",
    "NZD": "NZD",
    "AED": "AED",
}


def _normalize_currency(curr_str: str) -> str:
    """Normalize user input or currency name to 3-letter ISO code."""
    if not curr_str:
        return ""
    clean = curr_str.strip().upper()
    return CURRENCY_ALIASES.get(clean, clean)


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
) -> Dict[str, Any]:
    """
    Convert an amount from one currency to another using the Frankfurter API.

    Args:
        amount (float): The numeric amount to convert (e.g. 100).
        from_currency (str): Base currency code or name (e.g. 'USD', 'EUR', 'INR').
        to_currency (str): Target currency code or name (e.g. 'INR', 'EUR', 'USD').

    Returns:
        Dict[str, Any]: Conversion result including rate, converted amount, and formatted summary.
    """
    try:
        amount_num = float(amount)
        if amount_num < 0:
            return {
                "success": False,
                "error": "Amount must be a non-negative number.",
                "data": None
            }
    except (ValueError, TypeError):
        return {
            "success": False,
            "error": f"Invalid amount '{amount}'. Please provide a valid numeric value.",
            "data": None
        }

    base = _normalize_currency(from_currency)
    target = _normalize_currency(to_currency)

    if not base or not target:
        return {
            "success": False,
            "error": "Both 'from_currency' and 'to_currency' must be specified (e.g., from USD to INR).",
            "data": None
        }

    if base == target:
        return {
            "success": True,
            "amount": amount_num,
            "from_currency": base,
            "to_currency": target,
            "converted_amount": amount_num,
            "rate": 1.0,
            "date": "current",
            "formatted": f"{amount_num:.2f} {base} = {amount_num:.2f} {target} (Rate: 1.0000)",
            "error": None
        }

    # Frankfurter API endpoint
    api_url = "https://api.frankfurter.dev/v1/latest"
    params = {
        "amount": amount_num,
        "base": base,
        "symbols": target
    }

    try:
        response = requests.get(api_url, params=params, timeout=10)
        logger.debug(f"Frankfurter API response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            converted_val = rates.get(target)

            if converted_val is not None:
                unit_rate = converted_val / amount_num if amount_num > 0 else 0
                return {
                    "success": True,
                    "amount": amount_num,
                    "from_currency": base,
                    "to_currency": target,
                    "converted_amount": round(converted_val, 2),
                    "unit_rate": round(unit_rate, 4),
                    "date": data.get("date", ""),
                    "formatted": f"{amount_num:,.2f} {base} = {converted_val:,.2f} {target} (1 {base} = {unit_rate:.4f} {target})",
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "error": f"Target currency '{target}' is not supported or not found in rates.",
                    "data": None
                }

        elif response.status_code == 404:
            return {
                "success": False,
                "error": f"Currency conversion from '{base}' to '{target}' is not supported. Supported currencies include USD, EUR, INR, GBP, JPY, CAD, AUD, CHF, etc.",
                "data": None
            }
        else:
            return {
                "success": False,
                "error": f"Frankfurter API returned error status {response.status_code}.",
                "data": None
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Currency conversion request timed out. Please try again.",
            "data": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network error during currency conversion: {str(e)}",
            "data": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error in currency converter: {str(e)}",
            "data": None
        }


# Tool specification for LLM tool calling
CURRENCY_TOOL_DEFINITION = {
    "name": "convert_currency",
    "description": "Converts currency amounts between different international currencies (e.g. USD, EUR, INR, GBP, JPY, AUD, CAD) using real-time exchange rates. Use this tool whenever the user asks to convert currencies or exchange rates.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "amount": {
                "type": "NUMBER",
                "description": "The amount to convert (e.g. 100)"
            },
            "from_currency": {
                "type": "STRING",
                "description": "The source currency code or name (e.g. 'USD', 'EUR', 'INR', 'GBP')"
            },
            "to_currency": {
                "type": "STRING",
                "description": "The target currency code or name (e.g. 'INR', 'USD', 'EUR', 'JPY')"
            }
        },
        "required": ["amount", "from_currency", "to_currency"]
    }
}
