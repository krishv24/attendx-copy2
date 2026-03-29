# Autonomous Agent Architecture Plan

Currently, your project uses **CrewAI** with a `Process.sequential` configuration and `allow_delegation=False`. This effectively acts as a strict "assembly line" (pipeline), where Agent A finishes and hands off to Agent B, then to Agent C, in a hardcoded order. 

To meet your professor's requirement for **independent, autonomous agents**, the system needs to move away from a rigid pipeline to a setup where agents make their own decisions on *when* to act, *how* to communicate, and *what* to do based on dynamic conditions.

---

## 🏗️ How to Implement Autonomous Agents Here

There are three primary ways to implement this in your existing codebase, ranging from quick adjustments to larger software architecture changes:

### Approach 1: CrewAI Hierarchical & Delegation (Easiest)
You can maintain your use of CrewAI but change how the agents are orchestrated.
1. **Enable Delegation:** Set `allow_delegation=True` in agents like `prediction_agent` or `risk_scoring_agent`. This allows an agent to autonomously ask another agent for clarification or data, rather than waiting for its strict turn.
2. **Hierarchical Process:** Change `Process.sequential` to `Process.hierarchical` in [attendance_crew.py](file:///c:/Users/Krish%20Vinod/Desktop/Vs/attendance_ai/crew/attendance_crew.py). 
   - This automatically introduces an unseen "Manager Agent" (or you can define one).
   - The Manager looks at the goal (e.g., "Analyze today's attendance") and autonomously delegates tasks to the 8 agents in real-time, deciding the order based on intermediate results rather than a fixed script.

### Approach 2: Event-Driven Agent Microservices (Most "Independent")
To make them truly independent, decouple them from a single central orchestrator entirely.
1. **Event Bus / Triggers:** Agents sit idle and "listen" for specific events. (e.g., via SQLite/MySQL database triggers, or a message queue like RabbitMQ or Celery).
2. **Autonomous Activation:**
   - The *Data Ingestion Agent* runs when a new CSV is uploaded.
   - If it detects a sudden drop in a student's attendance, it emits a "High Risk Candidate" event.
   - The *Risk Scoring Agent* and *Alert Agent* wake up autonomously because they subscribe to that event, without needing a manager.
3. **Implementation:** Python wrapper scripts for each agent that poll the database or an event queue.

### Approach 3: State-Graph Routing (LangGraph approach)
Migrate the orchestrator from CrewAI to a graph-based framework like LangGraph.
- You treat agents as nodes on a graph. The edges of the graph are conditional logic ("Does the data contain an anomaly?").
- Agents can enter autonomous loops to self-correct and verify their own work before passing it along.

---

## 💰 Is it Feasible with Free Plans?

**Short Answer:** It is feasible, but **very challenging** without strict safeguards. Autonomous agents are extremely token-greedy and hit rate limits incredibly fast.

### The Challenge with Free Plans
An autonomous agent doesn't just make one prompt and get one answer. It uses a dynamic "Thought → Action (Tool) → Observation → Final Output" loop. If an agent delegates a task to another agent, they converse back and forth.
- **Rate Limits:** In your current code, you use `time.sleep(15)` specifically to avoid hitting free-tier limits (like Gemini's 15 Requests Per Minute limit).
- If your agents act autonomously and in parallel, they will easily try to make 20-30 requests per minute, resulting in `429 Too Many Requests` API errors crashing the agents.

### Feasibility Mitigation Strategies (How to make it work):

1. **Global Rate Limiter (Queueing)**
   - Because you can't rely on `time.sleep(15)` in a parallel/autonomous setup, you must implement a centralized "LLM Request Queue". Every agent must send its LLM request to this queue, which strictly processes them at a safe speed (e.g., 1 request every 5 seconds).
2. **Key Rotation (Already partially implemented)**
   - You currently have `api_key1` and `api_key2`. For true autonomous behavior on free tiers, dynamically distributing the workload across multiple developer API keys is necessary to avoid rate limits.
3. **Local LLMs for Simpler Agents (Hybrid Approach)**
   - Shift the simpler agents (like *Data Ingestion* and *Alert Notification*) to a localized, free AI model running on your computer using **Ollama** (e.g., Llama 3 8B or Mistral).
   - Reserve the precious Gemini/Groq free tier API limits strictly for agents requiring heavy reasoning (like *Risk Scoring* or *Prediction*).
4. **Aggressive Caching**
   - You already use `ai_cache.py`. You'll need to expand this so that independent agents communicating frequently don't burn API quota by asking the same questions repeatedly.
