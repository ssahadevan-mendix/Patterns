import anthropic
import json
from typing import Any

# Initialize the Anthropic client
client = anthropic.Anthropic()

# ─── Tool Definitions ─────────────────────────────────────────────────────────

def search_web(query: str) -> str:
    """Simulated web search tool."""
    results = {
        "python asyncio": "Python asyncio is a library for writing concurrent code using async/await syntax. It provides an event loop for running coroutines.",
        "react pattern ai": "ReAct (Reason + Act) is an AI prompting pattern that combines chain-of-thought reasoning with action execution in an interleaved manner.",
        "machine learning basics": "Machine learning is a subset of AI where systems learn from data. Key concepts: supervised learning, unsupervised learning, neural networks.",
    }
    for key in results:
        if key.lower() in query.lower():
            return results[key]
    return f"Search results for '{query}': Found several articles about this topic. The main concepts involve systematic approaches and best practices."

def calculate(expression: str) -> str:
    """Safe calculator tool."""
    try:
        allowed_chars = set("0123456789+-*/()., ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error: {str(e)}"

def get_weather(city: str) -> str:
    """Simulated weather tool."""
    weather_data = {
        "london": "London: 15°C, Partly Cloudy, Humidity: 72%",
        "new york": "New York: 22°C, Sunny, Humidity: 45%",
        "tokyo": "Tokyo: 28°C, Clear, Humidity: 60%",
        "paris": "Paris: 18°C, Overcast, Humidity: 68%",
    }
    return weather_data.get(city.lower(), f"{city}: 20°C, Clear skies, Humidity: 55%")

# ─── Tool Registry ─────────────────────────────────────────────────────────────

TOOLS = {
    "search_web": search_web,
    "calculate": calculate,
    "get_weather": get_weather,
}

# Anthropic tool schemas
TOOL_SCHEMAS = [
    {
        "name": "search_web",
        "description": "Search the web for information on a given topic or question.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "calculate",
        "description": "Evaluate a mathematical expression and return the result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression, e.g. '(3 + 5) * 2'"}
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'London'"}
            },
            "required": ["city"],
        },
    },
]

# ─── ReAct Agent ───────────────────────────────────────────────────────────────

def run_react_agent(user_query: str, max_iterations: int = 10) -> str:
    """
    ReAct Agent loop:
      1. REASON  – Claude thinks about what to do next
      2. ACT     – Claude calls a tool (if needed)
      3. OBSERVE – We run the tool and feed results back
      Repeat until Claude returns a final text answer.
    """
    print(f"\n{'='*60}")
    print(f"USER QUERY: {user_query}")
    print(f"{'='*60}\n")

    messages = [{"role": "user", "content": user_query}]

    for iteration in range(max_iterations):
        print(f"--- Iteration {iteration + 1} ---")

        # ── REASON: ask Claude what to do ──────────────────────────────
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        print(f"Stop reason: {response.stop_reason}")

        # ── Final answer: no more tool calls ──────────────────────────
        if response.stop_reason == "end_turn":
            final_text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "No response generated.",
            )
            print(f"\n✅ FINAL ANSWER:\n{final_text}")
            return final_text

        # ── ACT + OBSERVE: execute every tool Claude requested ────────
        if response.stop_reason == "tool_use":
            # Append Claude's full response (may contain text + tool_use blocks)
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    print(f"\n🔧 TOOL CALL: {tool_name}")
                    print(f"   Input: {json.dumps(tool_input, indent=2)}")

                    # Execute the tool
                    tool_fn = TOOLS.get(tool_name)
                    if tool_fn:
                        observation = tool_fn(**tool_input)
                    else:
                        observation = f"Error: Tool '{tool_name}' not found."

                    print(f"   Observation: {observation}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": observation,
                    })

            # Feed all observations back so Claude can reason further
            messages.append({"role": "user", "content": tool_results})

    return "Max iterations reached without a final answer."


# ─── Example Queries ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    queries = [
        "What's the weather in Tokyo and Paris? Which city is warmer?",
        "What is 15% of 2847, and then add 342 to that result?",
        "Search for information about the ReAct AI pattern and summarize it briefly.",
    ]

    for query in queries:
        result = run_react_agent(query)
        print(f"\n{'='*60}\n")
