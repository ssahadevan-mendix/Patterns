
Repo for AI Patterns

1. ReasonAct pattern:

How it works
The agent runs a tight Reason → Act → Observe loop:
User Query
    │
    ▼
┌─────────────────────────────────┐
│  REASON  Claude decides what    │
│          to do next             │
└────────────┬────────────────────┘
             │  tool_use?
    ┌────────▼────────┐     No (end_turn)
    │  ACT  Call the  │──────────────────► Final Answer
    │  real tool fn   │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  OBSERVE  Feed  │
    │  result back    │
    └────────┬────────┘
             │
             └──────────► (loop back to REASON)
Component	What it does
Tool schemas	Tell Claude what tools exist and how to call them
messages list	Acts as the agent's memory across iterations
stop_reason	tool_use → keep looping; end_turn → done
Tool executor	Dispatches calls to real Python functions and captures output
Key design choices
•	Multi-tool per turn — Claude can request several tools in one response; all results are batched and returned together
•	Full message history — every assistant reply and tool result is kept in messages, giving Claude full context across iterations
•	Max iterations guard — prevents infinite loops if Claude gets stuck
To use with real tools, just replace the simulated functions (search_web, get_weather, etc.) with actual API calls.




