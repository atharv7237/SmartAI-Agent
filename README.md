# Production-Ready MVP AI Tool-Calling Agent

An intelligent, conversational AI agent built in Python that understands user natural-language requests, autonomously decides which tool is required, executes that tool safely, receives the structured result, and synthesizes a natural-language response.

---

## 🏗️ Architecture

The agent follows the strict tool-calling lifecycle:

```text
               User Natural Language Request
                            ↓
                    LLM Agent (Gemini)
                            ↓
                     Tool Selection
             ┌──────────┬──────────┬──────────┬──────────┐
             ↓          ↓          ↓          ↓
        Calculator   Weather   Text Util   Currency
             │          │          │          │
             └──────────┴──────────┴──────────┘
                            ↓
                    Tool Execution
                            ↓
                    Structured Result
                            ↓
                    LLM Agent (Gemini)
                            ↓
                 Natural Language Response
```

---

## 🛠️ Available Tools

### 1. 🧮 Calculator (`tools/calculator.py`)
- **Capability**: Safe mathematical evaluation using AST parsing (no arbitrary code execution). Supports basic arithmetic (`+`, `-`, `*`, `/`), exponentiation (`^`), percentages (e.g. `15% of 800`), parentheses, and math functions (`sqrt`, `abs`, `round`).
- **Edge Cases Handled**: Division by zero, malformed expressions, invalid variables.

### 2. 🌦️ Weather Lookup (`tools/weather.py`)
- **Capability**: Real-time global weather lookup via the Open-Meteo API with integrated geocoding (no API key required). Fetches temperature (°C), weather condition, wind speed, and direction.
- **Edge Cases Handled**: Non-existent locations, geocoding failures, API timeouts.

### 3. 📝 Word / Text Utility (`tools/text_utils.py`)
- **Capability**: Text analysis and transformation tool. Supports word count, character count (total & excluding spaces), string reversal, and case transformation.
- **Edge Cases Handled**: Empty strings, strings with special whitespace, punctuation.

### 4. 💱 Currency Converter (`tools/currency.py`) - *Extension Tool*
- **Capability**: Real-time currency conversions via the Frankfurter API (no API key required). Converts amounts between major global currencies (USD, EUR, INR, GBP, JPY, CAD, AUD, etc.) with up-to-date exchange rates.
- **Edge Cases Handled**: Unsupported currency codes, negative amounts, identical currencies.

---

## 🚀 Setup & Installation

### 1. Clone or Open Workspace
```bash
cd hackathon
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the root directory (or copy from `.env.example`):
```bash
cp .env.example .env
```
Edit `.env` and insert your free Google Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
```
> 💡 *You can get a free Gemini API key in seconds from [Google AI Studio](https://aistudio.google.com/).*

---

## 💻 Running the Application

### 🌐 Modern Web Frontend (Recommended)
Launch the interactive web UI in your browser:
```bash
python server.py
# Or:
python main.py --web
```
Then open `http://localhost:8000` in any browser!

### Interactive CLI Mode (Live Gemini LLM)
```bash
python main.py
```

### Local Development / Mock Mode (Zero Gemini API Quota Consumed)
Test all tools, logic, and pipelines freely without using API keys or hitting quota limits:
```bash
python main.py --mock
# Or web interface in dev mode:
python server.py --mock
```
*(Or inside the interactive session, type `mock` to switch to offline mode and `live` to switch back).*

### 2-Minute Automated Demo Mode
```bash
python main.py --demo
```
*(Or type `demo` while inside the interactive CLI session)*

### Run Automated Unit Tests
```bash
python test_agent.py
```

---

## 💬 Example Prompts to Try

| Tool / Mode | Example User Prompt | Expected Agent Action |
|---|---|---|
| **Calculator** | `"What is 25 * 40?"` | Calls `calculate(expression="25 * 40")` -> `1000` |
| **Calculator** | `"Calculate 15% of 800"` | Calls `calculate(expression="15% of 800")` -> `120` |
| **Weather** | `"What's the weather in Mumbai?"` | Calls `get_weather(location="Mumbai")` -> Temperature & Condition |
| **Weather** | `"What is the current temperature in Delhi?"` | Calls `get_weather(location="Delhi")` |
| **Text Utility** | `"Count the words in 'AI is changing the world.'"` | Calls `text_operations(text=..., operation="word_count")` -> `5 words` |
| **Text Utility** | `"Reverse 'Hello World'"` | Calls `text_operations(text="Hello World", operation="reverse")` -> `dlroW olleH` |
| **Currency Converter** | `"Convert 100 USD to INR"` | Calls `convert_currency(amount=100, from_currency="USD", to_currency="INR")` |
| **General Chat** | `"Hello! Who are you and what can you do?"` | Directly responds conversationally without tools |
| **Edge Case (Math)** | `"What is 25 divided by 0?"` | Returns friendly explanation instead of crashing |
| **Edge Case (Weather)** | `"What's the weather in NonExistentCity999?"` | Informs user city could not be found |

---

## 🛡️ Error Handling & Reliability

- **Safe Math**: Evaluates AST node by node rather than using unsafe `eval()`.
- **Cross-Platform Resilient**: Gracefully reconfigures UTF-8 encoding on Windows terminals to prevent character encoding exceptions.
- **Graceful Fallbacks**: API timeouts, HTTP error codes, and bad inputs return user-friendly structured error messages without exposing Python stack traces.
- **Security**: `.gitignore` is pre-configured so secrets and `.env` files are never committed.
