How it works

Architecture:

User Task
    │
    ▼
┌─────────────────────────────────────────┐
│         ORCHESTRATOR AGENT              │
│   Coordinates pipeline & synthesizes   │
└──────┬──────────┬──────────┬───────────┘
       │          │          │
       ▼          ▼          ▼
  ┌─────────┐ ┌─────────┐ ┌─────────┐
  │Research │ │Analysis │ │ Writer  │
  │ Agent   │ │ Agent   │ │ Agent   │
  │         │ │         │ │         │
  │search   │ │analyze  │ │generate │
  │fact_chk │ │calc_    │ │_report_ │
  │         │ │metrics  │ │section  │
  └────┬────┘ └────┬────┘ └────┬────┘
       │           │           │
       └─────┬─────┘           │
             │   (context)     │
             └────────────────►│
                               │
                        Final Report

Key Design Patterns
PatternDescriptionSpecializationEach agent has a focused role, unique tools, and tailored system promptContext passingOutputs flow sequentially — analysis gets research context, writer gets bothOrchestrationA coordinator agent plans, sequences, and synthesizes without tools of its ownMemory per agentEach agent maintains its own conversation history for multi-turn tool useTool isolationAgents only access tools relevant to their role — no cross-contamination
Extending this pattern

Parallel agents — Run Research + a separate Competitive-Intel agent concurrently with asyncio
Critic agent — Add a review step that fact-checks the Writer's report before delivery
Dynamic routing — Have the Orchestrator decide at runtime which agents to invoke based on task type



Prerequisites:

1. Install python
2. Add anthropic key to env.sh
3. Set up the enviornment
   . ./env.sh
4. pip install anthropic
5. pip install pip-system-certs

To Run:

python multiAgent.py


