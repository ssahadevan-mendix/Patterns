import anthropic
import json
from typing import Any
from datetime import datetime

client = anthropic.Anthropic()
MODEL = "claude-opus-4-7"

# ─── Shared Tool Implementations ──────────────────────────────────────────────

def search_web(query: str) -> str:
    mock_data = {
        "python": "Python is a high-level programming language. Latest version: 3.13. Key libraries: NumPy, Pandas, FastAPI.",
        "machine learning": "ML market growing 38% YoY. Top frameworks: PyTorch, TensorFlow, scikit-learn. GPT-4 and Claude dominate LLM space.",
        "cloud computing": "AWS holds 32% market share, Azure 22%, GCP 11%. Serverless and containers are dominant trends.",
        "cybersecurity": "Global cybercrime costs $8 trillion in 2023. Zero-trust architecture and AI-driven threat detection are top trends.",
        "blockchain": "Ethereum 2.0 reduces energy use by 99.95%. DeFi TVL at $50B. Enterprise blockchain adoption rising.",
    }
    for key, val in mock_data.items():
        if key in query.lower():
            return val
    return f"Research findings for '{query}': Significant growth observed with multiple competing solutions emerging in 2024."

def analyze_data(data: str, analysis_type: str) -> str:
    analyses = {
        "sentiment": f"Sentiment Analysis of '{data[:40]}...': Positive (65%), Neutral (25%), Negative (10%). Overall: Favorable.",
        "trends": f"Trend Analysis of '{data[:40]}...': Upward trajectory detected. 3 major inflection points. Forecast: continued growth.",
        "risks": f"Risk Analysis of '{data[:40]}...': High risks: 2, Medium: 5, Low: 8. Primary concern: market volatility.",
        "opportunities": f"Opportunity Analysis of '{data[:40]}...': 4 high-value opportunities identified. ROI potential: 150-300%.",
    }
    return analyses.get(analysis_type.lower(),
        f"Analysis ({analysis_type}) of data: Key patterns found. Recommend further investigation.")

def generate_report_section(title: str, content: str, format_type: str = "markdown") -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""
## {title}
*Generated: {timestamp} | Format: {format_type}*

{content}

---
*Section compiled by Report Agent*
"""

def fact_check(claim: str) -> str:
    return f"Fact-check: '{claim[:60]}...' — Verified ✓. Sources: 3 authoritative references confirm this. Confidence: High (92%)."

def calculate_metrics(data: str, metric_type: str) -> str:
    metrics = {
        "roi": "ROI Calculation: Investment $50K → Return $185K. ROI: 270%. Payback period: 8 months.",
        "growth": "Growth Metrics: MoM: +12%, QoQ: +38%, YoY: +127%. CAGR: 89%.",
        "efficiency": "Efficiency Score: 87/100. Bottlenecks identified: 3. Optimization potential: 23% improvement.",
        "market_share": "Market Share Analysis: Current: 8.3%. TAM: $4.2B. Realistic target: 15% within 18 months.",
    }
    return metrics.get(metric_type.lower(),
        f"Metrics ({metric_type}): Baseline established. Performance index: 0.78. Benchmark: Above average.")

# ─── Tool Schemas ──────────────────────────────────────────────────────────────

RESEARCH_TOOLS = [
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
        "name": "fact_check",
        "description": "Verify the accuracy of a specific claim or statement.",
        "input_schema": {
            "type": "object",
            "properties": {"claim": {"type": "string", "description": "The claim to verify"}},
            "required": ["claim"],
        },
    },
]

ANALYSIS_TOOLS = [
    {
        "name": "analyze_data",
        "description": "Analyze data for sentiment, trends, risks, or opportunities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data to analyze"},
                "analysis_type": {
                    "type": "string",
                    "description": "Type: sentiment, trends, risks, opportunities",
                },
            },
            "required": ["data", "analysis_type"],
        },
    },
    {
        "name": "calculate_metrics",
        "description": "Calculate business metrics like ROI, growth, efficiency, market_share.",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Input data for calculation"},
                "metric_type": {
                    "type": "string",
                    "description": "Metric type: roi, growth, efficiency, market_share",
                },
            },
            "required": ["data", "metric_type"],
        },
    },
]

WRITER_TOOLS = [
    {
        "name": "generate_report_section",
        "description": "Generate a formatted report section with a title and content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Section title"},
                "content": {"type": "string", "description": "Section content"},
                "format_type": {"type": "string", "description": "Format: markdown, html, plain"},
            },
            "required": ["title", "content"],
        },
    },
]

TOOL_REGISTRY = {
    "search_web": search_web,
    "fact_check": fact_check,
    "analyze_data": analyze_data,
    "calculate_metrics": calculate_metrics,
    "generate_report_section": generate_report_section,
}

# ─── Base Agent ────────────────────────────────────────────────────────────────

class Agent:
    def __init__(self, name: str, role: str, tools: list, system_prompt: str):
        self.name = name
        self.role = role
        self.tools = tools
        self.system_prompt = system_prompt
        self.memory: list[dict] = []   # conversation history

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        fn = TOOL_REGISTRY.get(tool_name)
        if not fn:
            return f"Error: Tool '{tool_name}' not found."
        try:
            return fn(**tool_input)
        except Exception as e:
            return f"Tool error: {e}"

    def run(self, task: str, context: str = "") -> str:
        """Run the agent on a task, looping until it produces a final answer."""
        print(f"\n{'─'*50}")
        print(f"🤖 AGENT: {self.name} ({self.role})")
        print(f"📋 TASK : {task[:80]}...")
        print(f"{'─'*50}")

        user_content = f"{task}\n\nContext:\n{context}" if context else task
        self.memory = [{"role": "user", "content": user_content}]

        for iteration in range(8):
            response = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                system=self.system_prompt,
                tools=self.tools if self.tools else [],
                messages=self.memory,
            )

            if response.stop_reason == "end_turn":
                answer = next(
                    (b.text for b in response.content if hasattr(b, "text")), ""
                )
                print(f"✅ {self.name} completed task.")
                return answer

            if response.stop_reason == "tool_use":
                self.memory.append({"role": "assistant", "content": response.content})
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        print(f"   🔧 {block.name}({list(block.input.keys())})")
                        observation = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": observation,
                        })

                self.memory.append({"role": "user", "content": tool_results})

        return "Agent reached max iterations."


# ─── Specialized Agents ────────────────────────────────────────────────────────

class ResearchAgent(Agent):
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            role="Information Gatherer",
            tools=RESEARCH_TOOLS,
            system_prompt="""You are a meticulous research specialist. Your job is to:
1. Search for relevant, accurate information using available tools
2. Fact-check key claims before including them
3. Synthesize findings into a clear, structured research summary
4. Always cite what you found and from which search

Be thorough but concise. Structure output with clear sections.""",
        )


class AnalysisAgent(Agent):
    def __init__(self):
        super().__init__(
            name="AnalysisAgent",
            role="Data Analyst",
            tools=ANALYSIS_TOOLS,
            system_prompt="""You are an expert data analyst. Your job is to:
1. Analyze research findings using available analytical tools
2. Calculate relevant metrics (ROI, growth, market share)
3. Identify trends, risks, and opportunities
4. Provide data-driven insights and recommendations

Present findings with specific numbers and actionable insights.""",
        )


class WriterAgent(Agent):
    def __init__(self):
        super().__init__(
            name="WriterAgent",
            role="Report Compiler",
            tools=WRITER_TOOLS,
            system_prompt="""You are a professional business report writer. Your job is to:
1. Transform research and analysis into polished report sections
2. Use generate_report_section tool to format each major section
3. Ensure logical flow: Executive Summary → Findings → Analysis → Recommendations
4. Write clearly for executive-level audiences

Make the report compelling, scannable, and actionable.""",
        )


class OrchestratorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="OrchestratorAgent",
            role="Coordinator",
            tools=[],   # Orchestrator reasons only — no tools
            system_prompt="""You are a strategic project coordinator managing a team of AI agents.
Your job is to:
1. Break down complex tasks into sub-tasks for specialist agents
2. Determine the correct sequence: Research → Analysis → Report Writing
3. Synthesize agent outputs into a coherent final deliverable
4. Ensure nothing is missed and quality is high

Think step-by-step and coordinate agents in the right order.""",
        )

    def coordinate(self, task: str) -> str:
        """Orchestrate the full multi-agent pipeline."""
        print(f"\n{'='*60}")
        print(f"🎯 ORCHESTRATOR STARTING MULTI-AGENT PIPELINE")
        print(f"📌 TASK: {task}")
        print(f"{'='*60}")

        research_agent  = ResearchAgent()
        analysis_agent  = AnalysisAgent()
        writer_agent    = WriterAgent()

        # ── Step 1: Research ──────────────────────────────────────────
        research_task = f"Research the following topic thoroughly: {task}"
        research_output = research_agent.run(research_task)
        print(f"\n📚 RESEARCH COMPLETE — {len(research_output)} chars")

        # ── Step 2: Analysis ──────────────────────────────────────────
        analysis_task = (
            f"Analyze this research and extract key metrics, trends, risks, "
            f"and opportunities for: {task}"
        )
        analysis_output = analysis_agent.run(analysis_task, context=research_output)
        print(f"\n📊 ANALYSIS COMPLETE — {len(analysis_output)} chars")

        # ── Step 3: Write report ──────────────────────────────────────
        writer_task = (
            f"Write a comprehensive business report about: {task}\n"
            f"Create sections for: Executive Summary, Key Findings, "
            f"Data Analysis, Strategic Recommendations, and Conclusion."
        )
        combined_context = (
            f"RESEARCH:\n{research_output}\n\nANALYSIS:\n{analysis_output}"
        )
        report_output = writer_agent.run(writer_task, context=combined_context)
        print(f"\n📝 REPORT COMPLETE — {len(report_output)} chars")

        # ── Step 4: Orchestrator final synthesis ──────────────────────
        synthesis_task = f"""
You coordinated three agents to produce a report on: {task}

Research Summary (excerpt):
{research_output[:500]}

Analysis Summary (excerpt):
{analysis_output[:500]}

Final Report (excerpt):
{report_output[:500]}

Provide a brief pipeline summary: what each agent contributed, 
the overall quality of the output, and 2-3 key takeaways from the report.
"""
        synthesis = self.run(synthesis_task)

        return self._assemble_final_output(
            task, research_output, analysis_output, report_output, synthesis
        )

    def _assemble_final_output(
        self,
        task: str,
        research: str,
        analysis: str,
        report: str,
        synthesis: str,
    ) -> str:
        divider = "=" * 60
        return f"""
{divider}
MULTI-AGENT COLLABORATION — FINAL OUTPUT
Topic: {task}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{divider}

PIPELINE SUMMARY (Orchestrator)
{synthesis}

{divider}
RESEARCH AGENT OUTPUT
{divider}
{research}

{divider}
ANALYSIS AGENT OUTPUT
{divider}
{analysis}

{divider}
FINAL REPORT (Writer Agent)
{divider}
{report}
"""


# ─── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    orchestrator = OrchestratorAgent()

    final_report = orchestrator.coordinate(
        "The impact of AI and machine learning on the cybersecurity industry in 2024"
    )

    print(f"\n{'#'*60}")
    print("FULL MULTI-AGENT OUTPUT")
    print(f"{'#'*60}")
    print(final_report)

    # Save to file
    with open("multi_agent_report.md", "w") as f:
        f.write(final_report)
    print("\n💾 Report saved to multi_agent_report.md")
