import anthropic
import json
from typing import Any
from datetime import datetime

# Initialize the Anthropic client
client = anthropic.Anthropic()

# ─── Tool Definitions ─────────────────────────────────────────────────────────

def search_web(query: str) -> str:
    """Simulated web search tool."""
    results = {
        "python": "Python is a high-level programming language known for simplicity and readability. Used in web dev, data science, AI/ML.",
        "machine learning": "ML is a subset of AI. Key algorithms: linear regression, decision trees, neural networks, SVMs.",
        "climate change": "Global temperatures have risen ~1.1°C since pre-industrial times. Main causes: CO2 emissions, deforestation.",
        "stock market": "Markets involve buying/selling securities. Key indices: S&P 500, NASDAQ, Dow Jones.",
        "react pattern": "ReAct combines reasoning and acting. The agent thinks step-by-step and uses tools iteratively.",
    }
    for key in results:
        if key.lower() in query.lower():
            return results[key]
    return f"Search results for '{query}': Comprehensive information found covering history, applications, and current developments."

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
        "london": "London: 15°C, Partly Cloudy, Humidity: 72%, Wind: 12km/h",
        "new york": "New York: 22°C, Sunny, Humidity: 45%, Wind: 8km/h",
        "tokyo": "Tokyo: 28°C, Clear, Humidity: 60%, Wind: 5km/h",
        "paris": "Paris: 18°C, Overcast, Humidity: 68%, Wind: 15km/h",
        "sydney": "Sydney: 24°C, Partly Cloudy, Humidity: 55%, Wind: 20km/h",
    }
    return weather_data.get(city.lower(), f"{city}: 20°C, Clear skies, Humidity: 55%")

def get_current_time(timezone: str = "UTC") -> str:
    """Get current time for a timezone."""
    times = {
        "UTC": "14:30 UTC",
        "EST": "09:30 EST",
        "PST": "06:30 PST",
        "JST": "23:30 JST",
        "GMT": "14:30 GMT",
    }
    return times.get(timezone.upper(), f"Current time in {timezone}: 12:00")

def analyze_data(data: str, analysis_type: str) -> str:
    """Simulated data analysis tool."""
    analyses = {
        "summary": f"Summary of '{data}': Contains key metrics showing positive trends. Average values within expected ranges. 3 outliers detected.",
        "trend": f"Trend analysis of '{data}': Upward trend of 12% over the period. Seasonal patterns detected in Q2 and Q4.",
        "comparison": f"Comparison analysis of '{data}': Group A outperforms Group B by 23%. Statistical significance: p < 0.05.",
    }
    return analyses.get(analysis_type.lower(),
        f"Analysis of '{data}' ({analysis_type}): Completed successfully. Results show significant patterns worth investigating.")

# ─── Tool Registry ─────────────────────────────────────────────────────────────

TOOLS = {
    "search_web": search_web,
    "calculate": calculate,
    "get_weather": get_weather,
    "get_current_time": get_current_time,
    "analyze_data": analyze_data,
}

TOOL_SCHEMAS = [
    {
        "name": "search_web",
        "description": "Search the web for information on a topic.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    },
    {
        "name": "calculate",
        "description": "Evaluate a mathematical expression.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Math expression e.g. '10 * 1.15'"}},
            "required": ["expression"],
        },
    },
    {
        "name": "get_weather",
        "description": "Get current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name"}},
            "required": ["city"],
        },
    },
    {
        "name": "get_current_time",
        "description": "Get the current time for a timezone.",
        "input_schema": {
            "type": "object",
            "properties": {"timezone": {"type": "string", "description": "Timezone code e.g. 'UTC', 'EST'"}},
            "required": ["timezone"],
        },
    },
    {
        "name": "analyze_data",
        "description": "Analyze a dataset with a specified analysis type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Dataset name or description"},
                "analysis_type": {"type": "string", "description": "Type: 'summary', 'trend', or 'comparison'"},
            },
            "required": ["data", "analysis_type"],
        },
    },
]

# ─── Phase 1: PLANNER ─────────────────────────────────────────────────────────

def create_plan(user_query: str) -> list[dict]:
    """
    Planner phase: ask Claude to decompose the query into
    a numbered list of concrete, sequential steps.
    """
    print(f"\n{'='*60}")
    print("📋 PLANNING PHASE")
    print(f"{'='*60}")

    planning_prompt = f"""You are a planning agent. Break down the following task into clear, sequential steps.

Task: {user_query}

Available tools:
- search_web(query): Search for information
- calculate(expression): Perform math calculations  
- get_weather(city): Get weather for a city
- get_current_time(timezone): Get current time
- analyze_data(data, analysis_type): Analyze datasets

Return a JSON array of steps. Each step must have:
- "step_id": integer (1, 2, 3...)
- "description": what this step accomplishes
- "tool": which tool to use (or "synthesize" for the final answer step)
- "depends_on": list of step_ids this step needs results from ([] if none)
- "reasoning": why this step is necessary

Respond with ONLY valid JSON, no markdown fences or extra text."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": planning_prompt}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    plan = json.loads(raw)

    print(f"\nGenerated {len(plan)} steps:\n")
    for step in plan:
        deps = f" (needs steps {step['depends_on']})" if step["depends_on"] else ""
        print(f"  Step {step['step_id']}: {step['description']}")
        print(f"           Tool: {step['tool']}{deps}")
        print(f"           Why:  {step['reasoning']}\n")

    return plan


# ─── Phase 2: EXECUTOR ────────────────────────────────────────────────────────

def execute_plan(plan: list[dict], user_query: str) -> str:
    """
    Executor phase: run each step in dependency order,
    collecting results and feeding them forward.
    """
    print(f"\n{'='*60}")
    print("⚙️  EXECUTION PHASE")
    print(f"{'='*60}\n")

    results: dict[int, str] = {}   # step_id → observation

    # ── topological sort (simple: iterate until all steps are done) ──
    completed = set()
    pending = list(plan)
    max_passes = len(plan) * 2

    for _ in range(max_passes):
        if not pending:
            break

        for step in list(pending):
            # Skip if dependencies aren't done yet
            if not all(dep in completed for dep in step["depends_on"]):
                continue

            sid = step["step_id"]
            tool_name = step["tool"]

            print(f"--- Step {sid}: {step['description']} ---")
            print(f"    Tool: {tool_name}")

            # ── Synthesis step: ask Claude to combine all results ──────
            if tool_name == "synthesize":
                context_parts = [f"Step {i}: {r}" for i, r in results.items()]
                context = "\n".join(context_parts)

                synthesis_prompt = f"""Original task: {user_query}

Results collected from previous steps:
{context}

Using these results, provide a comprehensive final answer to the original task.
Be specific, cite the data collected, and make the answer directly useful."""

                synthesis_response = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": synthesis_prompt}],
                )
                answer = synthesis_response.content[0].text
                results[sid] = answer
                print(f"    ✅ Synthesized final answer.\n")

            # ── Tool step: ask Claude which args to pass, then run it ──
            else:
                dep_context = ""
                if step["depends_on"]:
                    dep_context = "\n".join(
                        f"Step {d} result: {results[d]}" for d in step["depends_on"]
                    )

                arg_prompt = f"""You must call the tool '{tool_name}' to complete this step.

Step description: {step['description']}
{f'Context from previous steps:{chr(10)}{dep_context}' if dep_context else ''}

Call the '{tool_name}' tool now with appropriate arguments."""

                arg_response = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=512,
                    tools=TOOL_SCHEMAS,
                    messages=[{"role": "user", "content": arg_prompt}],
                )

                # Extract and run the tool call
                observation = f"Tool '{tool_name}' produced no output."
                for block in arg_response.content:
                    if block.type == "tool_use" and block.name == tool_name:
                        tool_fn = TOOLS.get(tool_name)
                        if tool_fn:
                            observation = tool_fn(**block.input)
                            print(f"    Args:   {json.dumps(block.input)}")
                        break

                results[sid] = observation
                print(f"    Result: {observation}\n")

            completed.add(sid)
            pending.remove(step)
            break   # restart the outer loop after each completion

    # Return the synthesis step's output, or the last result
    last_sid = max(results.keys())
    return results[last_sid]


# ─── Top-level runner ─────────────────────────────────────────────────────────

def run_plan_and_execute(user_query: str) -> str:
    """Full Plan-and-Execute pipeline."""
    plan    = create_plan(user_query)
    answer  = execute_plan(plan, user_query)

    print(f"\n{'='*60}")
    print("✅ FINAL ANSWER")
    print(f"{'='*60}")
    print(answer)
    return answer


# ─── Example Queries ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    queries = [
        "Compare the weather in Tokyo and London, calculate the temperature difference, and tell me which city is better for outdoor activities today.",
        "Search for information about machine learning, then analyze the 'ML adoption trends 2024' dataset for trends, and summarize the findings.",
        "What time is it in EST and JST? Calculate how many hours apart those timezones are.",
    ]

    for query in queries:
        run_plan_and_execute(query)
        print("\n" + "="*60 + "\n")
