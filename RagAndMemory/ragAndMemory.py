import os
import json
import time
import math
import anthropic
from typing import Any
from datetime import datetime

# ─── Anthropic Client ─────────────────────────────────────────────────────────

client = anthropic.Anthropic()

# ─── In-Memory Vector Store (no external DB needed) ───────────────────────────

class SimpleVectorStore:
    """
    Lightweight vector store using TF-IDF-style cosine similarity.
    In production, swap this for ChromaDB, Pinecone, pgvector, etc.
    """

    def __init__(self):
        self.documents: list[dict] = []   # {id, text, metadata, embedding}

    # ── Embed via Claude (reuse-friendly) ──────────────────────────────────
    def _embed(self, text: str) -> list[float]:
        """
        Produce a bag-of-words TF vector for quick local similarity.
        Replace with a real embedding model (e.g. text-embedding-3-small)
        for semantic search in production.
        """
        words = text.lower().split()
        vocab = list(set(words))
        vec = [words.count(w) for w in vocab]
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec], vocab

    def _cosine_similarity(self, vec_a: tuple, vec_b: tuple) -> float:
        a_vals, a_vocab = vec_a
        b_vals, b_vocab = vec_b
        # Align on shared vocabulary
        shared = set(a_vocab) & set(b_vocab)
        if not shared:
            return 0.0
        a_map = dict(zip(a_vocab, a_vals))
        b_map = dict(zip(b_vocab, b_vals))
        dot = sum(a_map[w] * b_map[w] for w in shared)
        return dot

    def add_document(self, doc_id: str, text: str, metadata: dict = None):
        vec, vocab = self._embed(text)
        self.documents.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {},
            "embedding": (vec, vocab),
        })
        print(f"  📄 Indexed: [{doc_id}] {text[:60]}...")

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        q_vec = self._embed(query)
        scored = [
            (doc, self._cosine_similarity(q_vec, doc["embedding"]))
            for doc in self.documents
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {"id": d["id"], "text": d["text"], "metadata": d["metadata"], "score": s}
            for d, s in scored[:top_k]
            if s > 0
        ]


# ─── Memory Layers ────────────────────────────────────────────────────────────

class ConversationMemory:
    """Short-term: sliding window of recent messages."""

    def __init__(self, window: int = 10):
        self.window = window
        self.messages: list[dict] = []   # {role, content, timestamp}

    def add(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self.messages) > self.window:
            self.messages.pop(0)

    def get_context(self) -> list[dict]:
        """Return plain {role, content} dicts for the API."""
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    def __len__(self):
        return len(self.messages)


class EpisodicMemory:
    """Long-term: compressed summaries of past sessions."""

    def __init__(self):
        self.episodes: list[dict] = []   # {summary, key_facts, timestamp}


    def _call_llm_for_summary(self, history: list[dict]) -> str:
        """Summarize a conversation history using Claude."""
        
        # Format the conversation history into readable text
        formatted = "\n".join(
            f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
            for msg in history
        )
        
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Summarize the following conversation concisely, "
                        "capturing the key topics, decisions, and outcomes:\n\n"
                        f"{formatted}"
                    ),
                }
            ],
        )
        
        return response.content[0].text

    def store_episode(self, history):
        raw = self._call_llm_for_summary(history)  # uses updated prompt above

    	# 1. Strip whitespace
        raw = raw.strip()

    	# 2. Remove markdown fences
        if raw.startswith("```"):
       	 	parts = raw.split("```")
       	 	raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

    	# 3. Parse with fallback
        try:
        	episode = json.loads(raw)
        except json.JSONDecodeError as e:
        	print(f"[Warning] Could not parse episode JSON: {e}")
        	episode = {
            		"summary": raw[:500],
            		"history": history,
            		"error": str(e)
        	}

        return episode

    def get_relevant(self, query: str, top_k: int = 2) -> list[dict]:
        """Very simple recency-based retrieval — swap for vector search in prod."""
        return self.episodes[-top_k:] if self.episodes else []


class WorkingMemory:
    """Ultra-short: current reasoning context (entities, goals, constraints)."""

    def __init__(self):
        self.entities: dict[str, str] = {}   # name → description
        self.current_goal: str = ""
        self.constraints: list[str] = []

    def update(self, key: str, value: Any):
        if key == "goal":
            self.current_goal = value
        elif key == "constraint":
            self.constraints.append(value)
        else:
            self.entities[key] = str(value)

    def to_string(self) -> str:
        parts = []
        if self.current_goal:
            parts.append(f"Goal: {self.current_goal}")
        if self.entities:
            ents = "; ".join(f"{k}={v}" for k, v in self.entities.items())
            parts.append(f"Entities: {ents}")
        if self.constraints:
            parts.append(f"Constraints: {', '.join(self.constraints)}")
        return " | ".join(parts) if parts else "None"


# ─── Knowledge Base (the "R" in RAG) ─────────────────────────────────────────

def build_knowledge_base(store: SimpleVectorStore):
    docs = [
        ("kb-001", "Python asyncio provides concurrent programming via async/await. Use asyncio.gather() to run coroutines in parallel.", {"category": "python"}),
        ("kb-002", "RAG (Retrieval-Augmented Generation) enhances LLMs by injecting relevant external documents into the prompt at inference time.", {"category": "ai"}),
        ("kb-003", "Vector databases store high-dimensional embeddings. Popular options: Pinecone, Weaviate, Qdrant, ChromaDB, pgvector.", {"category": "ai"}),
        ("kb-004", "Transformers use self-attention to weigh token relationships. BERT is encoder-only; GPT is decoder-only; T5 is encoder-decoder.", {"category": "ai"}),
        ("kb-005", "Python type hints (PEP 484) improve readability. Use `from __future__ import annotations` for forward references.", {"category": "python"}),
        ("kb-006", "Docker containers package apps with their dependencies. A Dockerfile defines the image; docker-compose orchestrates multiple services.", {"category": "devops"}),
        ("kb-007", "Memory in AI agents: working memory (current context), episodic memory (past events), semantic memory (general knowledge).", {"category": "ai"}),
        ("kb-008", "FastAPI is an async Python web framework. It auto-generates OpenAPI docs and uses Pydantic for request/response validation.", {"category": "python"}),
        ("kb-009", "Kubernetes orchestrates containers across a cluster. Key objects: Pod, Deployment, Service, Ingress, ConfigMap, Secret.", {"category": "devops"}),
        ("kb-010", "LLM fine-tuning adapts a pretrained model to a specific domain. LoRA (Low-Rank Adaptation) reduces VRAM by training small adapter layers.", {"category": "ai"}),
    ]
    print("📚 Building knowledge base...")
    for doc_id, text, meta in docs:
        store.add_document(doc_id, text, meta)
    print(f"✅ {len(docs)} documents indexed\n")


# ─── RAG + Memory Agent ───────────────────────────────────────────────────────

class RAGMemoryAgent:
    def __init__(self):
        self.vector_store   = SimpleVectorStore()
        self.conv_memory    = ConversationMemory(window=10)
        self.episodic_mem   = EpisodicMemory()
        self.working_mem    = WorkingMemory()
        self.session_count  = 0

        build_knowledge_base(self.vector_store)

    # ── Retrieve ───────────────────────────────────────────────────────────
    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        results = self.vector_store.search(query, top_k=top_k)
        print(f"\n🔍 Retrieved {len(results)} doc(s) for: '{query}'")
        for r in results:
            print(f"   [{r['id']}] score={r['score']:.3f} | {r['text'][:70]}...")
        return results

    # ── Build system prompt ────────────────────────────────────────────────
    def _build_system_prompt(self, retrieved_docs: list[dict]) -> str:
        rag_context = "\n\n".join(
            f"[{d['id']}] {d['text']}" for d in retrieved_docs
        ) or "No relevant documents found."

        past_episodes = self.episodic_mem.get_relevant("", top_k=2)
        episode_text = "\n".join(
            f"- {ep['summary']}" for ep in past_episodes
        ) or "No past sessions."

        return f"""You are a knowledgeable AI assistant with access to a curated knowledge base and memory of past interactions.

=== RETRIEVED KNOWLEDGE ===
{rag_context}

=== PAST SESSION SUMMARIES ===
{episode_text}

=== WORKING MEMORY ===
{self.working_mem.to_string()}

Instructions:
- Ground answers in the retrieved knowledge when relevant.
- Reference past sessions if they contain useful context.
- Be concise and accurate.
- If the knowledge base doesn't cover a topic, say so honestly."""

    # ── Single turn ────────────────────────────────────────────────────────
    def chat(self, user_input: str) -> str:
        print(f"\n{'─'*55}")
        print(f"👤 USER: {user_input}")

        # Retrieve relevant docs
        docs = self.retrieve(user_input)

        # Update working memory with detected entities
        keywords = ["python", "docker", "kubernetes", "rag", "memory", "fastapi"]
        for kw in keywords:
            if kw in user_input.lower():
                self.working_mem.update(kw, "mentioned in query")

        # Add user message to conversation memory
        self.conv_memory.add("user", user_input)

        # Build messages list: system + conversation history
        system_prompt = self._build_system_prompt(docs)
        history = self.conv_memory.get_context()[:-1]  # exclude the message we just added

        messages = history + [{"role": "user", "content": user_input}]

        # Call Claude
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=600,
            system=system_prompt,
            messages=messages,
        )

        answer = response.content[0].text
        self.conv_memory.add("assistant", answer)

        print(f"\n🤖 ASSISTANT: {answer}")
        return answer

    # ── End session: compress conversation to episodic memory ──────────────
    def end_session(self):
        self.session_count += 1
        print(f"\n💾 Compressing session {self.session_count} to episodic memory...")
        history = self.conv_memory.get_context()
        if history:
            # print(f"    history: {history}")
            summary = self.episodic_mem.store_episode(history)
            print(f"   Summary: {summary}")
        self.conv_memory.messages.clear()
        print("   Conversation memory cleared.\n")


# ─── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    agent = RAGMemoryAgent()

    print("\n" + "═"*55)
    print("  SESSION 1 — Python & AI questions")
    print("═"*55)

    agent.chat("What is RAG and how does it work?")
    agent.chat("Which vector databases would you recommend and why?")
    agent.chat("How does memory work in AI agents?")
    agent.end_session()

    print("═"*55)
    print("  SESSION 2 — Follow-up (uses episodic memory)")
    print("═"*55)

    agent.chat("Can you remind me what we discussed about vector databases?")
    agent.chat("How does FastAPI compare to traditional Python web frameworks?")
    agent.end_session()
