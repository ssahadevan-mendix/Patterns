How it works
The pattern separates thinking from doing into two distinct phases:
User Query
    │
    ▼
┌──────────────────────────────────────┐
│  PLANNER  Claude reads the task and  │
│           outputs a JSON step list   │
│           with dependencies          │
└──────────────┬───────────────────────┘
               │  [ step list ]
    ┌──────────▼───────────────────────┐
    │  EXECUTOR  Runs steps in         │
    │  dependency order; feeds each    │
    │  result into the next step       │
    └──────────┬───────────────────────┘
               │  all results
    ┌──────────▼───────────────────────┐
    │  SYNTHESIZER  Claude combines    │
    │  all observations into a final   │
    │  coherent answer                 │
    └──────────────────────────────────┘
Plan vs. ReAct — when to use which
ReActPlan & ExecuteStructureDecide one step at a timeFull plan upfront, then executeAdaptabilityHigh — reacts to each observationLower — plan is fixedParallelismSequential onlySteps can run in parallel (via depends_on)TransparencyImplicit reasoningExplicit, inspectable planBest forOpen-ended explorationWell-defined multi-step tasks
Key design choices

Dependency graph — each step declares depends_on, enabling topological execution order and future parallelism
Two-model-call execution — one call to determine tool arguments, another for final synthesis; keeps concerns clean
Synthesizer step — the plan always ends with a "tool": "synthesize" step where Claude weaves all results into a coherent answer
Planner isolation — the planner has no tools and produces only JSON, making plans easy to inspect, log, or override



Prerequisites:

1. Install python
2. Add anthropic key to env.sh
3. Set up the enviornment
   . ./env.sh
4. pip install anthropic
5. pip install pip-system-certs

To Run:

python planAndExecute.py
