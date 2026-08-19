"""
Main CLI Application: Production-Ready MVP AI Tool-Calling Agent.
"""

import sys
import time
import argparse
from colorama import init, Fore, Style

from agent import AIAgent

# Configure standard encoding and colorama
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

init(autoreset=True)


BANNER = f"""
{Fore.CYAN}==================================================================
        🚀 Production-Ready AI Tool-Calling Agent MVP
=================================================================={Style.RESET_ALL}
{Fore.GREEN}Architecture:{Style.RESET_ALL}
  User Input -> LLM Agent -> Tool Selection -> Tool Execution -> Final Response

{Fore.YELLOW}Available Tools:{Style.RESET_ALL}
  1. 🧮 Calculator          (e.g., 'What is 25 * 40?', '15% of 800')
  2. 🌦️ Weather Lookup       (e.g., 'What is the weather in Mumbai?')
  3. 📝 Text Utility        (e.g., 'Reverse Hello World', 'Count words in...')
  4. 💱 Currency Converter   (e.g., 'Convert 100 USD to INR')

{Fore.MAGENTA}Commands:{Style.RESET_ALL}
  - Type {Fore.WHITE}'demo'{Fore.MAGENTA} to run an automated 2-minute showcase
  - Type {Fore.WHITE}'help'{Fore.MAGENTA} for usage tips
  - Type {Fore.WHITE}'clear'{Fore.MAGENTA} to reset conversation history
  - Type {Fore.WHITE}'exit'{Fore.MAGENTA} or {Fore.WHITE}'quit'{Fore.MAGENTA} to close
==================================================================
"""

DEMO_PROMPTS = [
    ("General Conversation", "Hello! Who are you and what tools can you use?"),
    ("Calculator Tool (Math)", "What is 25 * 40?"),
    ("Calculator Tool (Percentage)", "Calculate 15% of 800."),
    ("Weather Lookup Tool", "What's the weather in Mumbai?"),
    ("Text Utility (Reverse)", "Reverse the text: Hello World"),
    ("Text Utility (Word Count)", "Count the words in: AI is changing the world."),
    ("Currency Converter (Extension)", "Convert 100 USD to INR."),
    ("Edge Case Handling (Invalid Math)", "What is 25 divided by 0?"),
    ("Edge Case Handling (Invalid City)", "What is the weather in NonExistentCity999?"),
]


def print_tool_trace(tool_called: str, tool_args: dict, tool_result: dict) -> None:
    """Visually display the tool calling flow."""
    print(f"\n{Fore.YELLOW}─── [Tool Execution Pipeline] ───{Style.RESET_ALL}")
    print(f" {Fore.CYAN}▸ Tool Selected:{Style.RESET_ALL} {Fore.GREEN}{tool_called}{Style.RESET_ALL}")
    print(f" {Fore.CYAN}▸ Arguments:{Style.RESET_ALL}     {Fore.WHITE}{tool_args}{Style.RESET_ALL}")
    print(f" {Fore.CYAN}▸ Raw Result:{Style.RESET_ALL}    {Fore.LIGHTBLACK_EX}{tool_result}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}─────────────────────────────────{Style.RESET_ALL}\n")


def run_single_prompt(agent: AIAgent, prompt: str) -> None:
    """Execute a prompt and display results cleanly."""
    print(f"\n{Fore.GREEN}User:{Style.RESET_ALL} {prompt}")
    result = agent.run(prompt, verbose=False)

    if result.get("tool_called"):
        print_tool_trace(
            result["tool_called"],
            result.get("tool_args", {}),
            result.get("tool_result", {})
        )

    print(f"{Fore.CYAN}Agent:{Style.RESET_ALL} {result['response']}\n")


def run_demo(agent: AIAgent) -> None:
    """Run automated demo covering all tools and edge cases in under 2 minutes."""
    print(f"\n{Fore.YELLOW}=== Starting Automated 2-Minute Demo ==={Style.RESET_ALL}\n")

    for idx, (category, prompt) in enumerate(DEMO_PROMPTS, 1):
        print(f"{Fore.MAGENTA}[Demo Step {idx}/{len(DEMO_PROMPTS)}] - {category}{Style.RESET_ALL}")
        run_single_prompt(agent, prompt)
        if idx < len(DEMO_PROMPTS):
            time.sleep(4.0)

    print(f"{Fore.GREEN}=== Demo Complete! ==={Style.RESET_ALL}\n")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="AI Tool-Calling Agent MVP")
    parser.add_argument("--demo", action="store_true", help="Run automated showcase demo")
    parser.add_argument("--mock", action="store_true", help="Run in local development/mock mode without consuming Gemini API quota")
    parser.add_argument("--web", action="store_true", help="Launch the modern Web Frontend server")
    parser.add_argument("--port", type=int, default=8000, help="Port for the web server (default: 8000)")
    args = parser.parse_args()

    if args.web:
        from server import run_server
        run_server(port=args.port, mock_mode=True if args.mock else None)
        return

    agent = AIAgent(mock_mode=True if args.mock else None)
    print(BANNER)

    if agent.mock_mode:
        print(f"{Fore.CYAN}🟢 Mode: [LOCAL DEV / MOCK MODE - Zero Gemini API Quota Used]{Style.RESET_ALL}")
        print(f"All real tools (Calculator, Open-Meteo Weather, Frankfurter Currency, Text Utils) will execute locally.\n")
    elif not agent.is_configured():
        print(f"{Fore.YELLOW}[Warning] GEMINI_API_KEY is not set in .env.{Style.RESET_ALL}")
        print(f"You can add your key to {Fore.WHITE}.env{Fore.YELLOW} or run {Fore.WHITE}python main.py --mock{Fore.YELLOW} for offline testing.\n")
    else:
        print(f"{Fore.GREEN}🟢 Mode: [LIVE GEMINI LLM MODE - Model: {agent.model}]{Style.RESET_ALL}\n")

    if args.demo:
        run_demo(agent)
        return

    while True:
        try:
            user_input = input(f"{Fore.GREEN}You > {Style.RESET_ALL}").strip()
            if not user_input:
                continue

            lower_input = user_input.lower()

            if lower_input in ("exit", "quit", "q"):
                print(f"{Fore.CYAN}Goodbye! Have a great day.{Style.RESET_ALL}")
                break

            elif lower_input == "demo":
                run_demo(agent)
                continue

            elif lower_input == "mock":
                agent.mock_mode = True
                print(f"{Fore.CYAN}Switched to LOCAL DEV / MOCK MODE (Zero API quota used).{Style.RESET_ALL}\n")
                continue

            elif lower_input == "live":
                agent.mock_mode = False
                print(f"{Fore.GREEN}Switched to LIVE GEMINI LLM MODE.{Style.RESET_ALL}\n")
                continue

            elif lower_input == "clear":
                agent.reset_conversation()
                print(f"{Fore.YELLOW}Conversation history cleared.{Style.RESET_ALL}\n")
                continue

            elif lower_input == "help":
                print(f"""
{Fore.YELLOW}How to interact with the agent:{Style.RESET_ALL}
- Ask math questions: 'What is 25 * 40?' or '18% of 900'
- Inquire about weather: 'How is the weather in Paris?'
- Manipulate text: 'Count words in This is an example' or 'Reverse Antigravity'
- Convert currencies: 'Convert 250 EUR to USD'
- Type 'mock' to switch to offline zero-quota testing
- Type 'live' to switch to live Gemini LLM mode
                """)
                continue

            run_single_prompt(agent, user_input)

        except KeyboardInterrupt:
            print(f"\n{Fore.CYAN}Session interrupted. Exiting...{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"\n{Fore.RED}An error occurred: {str(e)}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
