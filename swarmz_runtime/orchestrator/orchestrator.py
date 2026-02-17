# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# -----------------------------
# Data models
# -----------------------------

@dataclass
class Agent:
    """
    Minimal agent descriptor.

    Lightweight and deterministic:
      - role/goal/backstory provide "persona"
      - tools is metadata for later routing (not required for v0)
    """
    name: str
    role: str
    goal: str
    backstory: str = ""
    tools: List[str] = field(default_factory=list)
    verbose: bool = True


@dataclass
class Task:
    """
    A unit of work assigned to a specific agent.
    """
    name: str
    description: str
    expected_output: str
    agent_name: str
    async_execution: bool = False


@dataclass
class CrewResult:
    tasks: List[Task]
    outputs: List[Dict[str, Any]]


# -----------------------------
# OpenAI Responses API client (stdlib-only)
# -----------------------------

class OpenAIResponsesClient:
    """
    Minimal OpenAI Responses API client using only stdlib (urllib).

    Env:
      OPENAI_API_KEY  (required to enable real calls)
      SWARMZ_MODEL    (optional, defaults to gpt-4.1-mini)
      OPENAI_BASE_URL (optional, defaults to https://api.openai.com/v1)
      SWARMZ_TIMEOUT_S (optional, defaults to 60)
      SWARMZ_RETRIES  (optional, defaults to 2)
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("SWARMZ_MODEL", "gpt-4.1-mini").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.timeout_s = int(os.getenv("SWARMZ_TIMEOUT_S", "60"))
        self.retries = int(os.getenv("SWARMZ_RETRIES", "2"))

    def enabled(self) -> bool:
        return bool(self.api_key)

    def create_response(self, prompt: str) -> Dict[str, Any]:
        url = f"{self.base_url}/responses"
        payload = {
            "model": self.model,
            "input": prompt,
        }

        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        last_err: Optional[str] = None
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(url, data=body, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw)

            except urllib.error.HTTPError as e:
                raw = ""
                try:
                    raw = e.read().decode("utf-8", errors="replace")
                except Exception:
                    pass

                # Backoff for 429 / 5xx
                if e.code in (429, 500, 502, 503, 504) and attempt < self.retries:
                    time.sleep(0.8 * (attempt + 1))
                    last_err = f"HTTP {e.code}: {raw or str(e)}"
                    continue

                raise RuntimeError(f"OpenAI Responses HTTPError {e.code}: {raw or str(e)}") from e

            except urllib.error.URLError as e:
                if attempt < self.retries:
                    time.sleep(0.6 * (attempt + 1))
                    last_err = str(e)
                    continue
                raise RuntimeError(f"OpenAI Responses URLError: {e}") from e

            except Exception as e:
                if attempt < self.retries:
                    time.sleep(0.6 * (attempt + 1))
                    last_err = str(e)
                    continue
                raise

        raise RuntimeError(f"OpenAI call failed after retries: {last_err or 'unknown error'}")


def _extract_output_text(resp: Dict[str, Any]) -> str:
    """
    Responses API returns:
      - top-level output_text (convenience)
      - and/or output[] messages with content parts of type output_text
    """
    if isinstance(resp, dict):
        ot = resp.get("output_text")
        if isinstance(ot, str) and ot.strip():
            return ot.strip()

        out = resp.get("output")
        if isinstance(out, list):
            parts: List[str] = []
            for item in out:
                if not isinstance(item, dict):
                    continue
                if item.get("type") != "message":
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "output_text":
                        t = c.get("text")
                        if isinstance(t, str) and t:
                            parts.append(t)
            joined = "\n".join(p.strip() for p in parts if p.strip())
            if joined.strip():
                return joined.strip()

    return ""


# -----------------------------
# Crew runner (now real)
# -----------------------------

class Crew:
    """
    Minimal "crew" runner.

    v0 behavior:
      - if OPENAI_API_KEY is set => real model calls per task
      - else => simulation mode (safe fallback)

    Later:
      - tool routing
      - multi-turn memory
      - graph execution / parallelism
    """

    def __init__(self, agents: List[Agent], tasks: List[Task], verbose: bool = True):
        self.agents = {a.name: a for a in agents}
        self.tasks = tasks
        self.verbose = verbose
        self.llm = OpenAIResponsesClient()

    def kickoff(self) -> CrewResult:
        outputs: List[Dict[str, Any]] = []

        for task in self.tasks:
            agent = self.agents.get(task.agent_name)
            if not agent:
                result = {"task": task.name, "error": f"Agent '{task.agent_name}' not found"}
                outputs.append(result)
                if self.verbose:
                    print(result["error"])
                continue

            if self.llm.enabled():
                prompt = self._build_prompt(agent=agent, task=task)
                try:
                    resp = self.llm.create_response(prompt)
                    text = _extract_output_text(resp)

                    if not text:
                        text = "[EMPTY_OUTPUT] Model returned no output_text."

                    result = {
                        "task": task.name,
                        "agent": agent.name,
                        "role": agent.role,
                        "description": task.description,
                        "expected_output": task.expected_output,
                        "result": text,
                        "provider": "openai_responses",
                        "model": self.llm.model,
                    }

                except Exception as e:
                    result = {
                        "task": task.name,
                        "agent": agent.name,
                        "role": agent.role,
                        "description": task.description,
                        "expected_output": task.expected_output,
                        "error": str(e),
                        "provider": "openai_responses",
                        "model": self.llm.model,
                    }

                outputs.append(result)
                if self.verbose:
                    ok = "OK" if "result" in result else "ERR"
                    print(f"[Crew] {agent.name} -> {task.name}: {ok}")

            else:
                # Simulation fallback (no key)
                simulated_output = {
                    "task": task.name,
                    "agent": agent.name,
                    "role": agent.role,
                    "description": task.description,
                    "expected_output": task.expected_output,
                    "result": f"[SIMULATED] {agent.role} executed task '{task.name}' (set OPENAI_API_KEY to enable real calls)",
                    "provider": "simulated",
                }
                outputs.append(simulated_output)
                if self.verbose:
                    print(f"[Crew] {agent.name} -> {task.name}: OK (SIM)")

        return CrewResult(tasks=self.tasks, outputs=outputs)

    def _build_prompt(self, agent: Agent, task: Task) -> str:
        # Simple, strong prompt contract: role â†’ goal â†’ task â†’ expected output.
        # Later we can convert to structured "input items" and add tool calls.
        tools = ", ".join(agent.tools) if agent.tools else "none"
        return (
            "You are operating inside SWARMZ.\n"
            "You must produce the expected output as directly as possible.\n\n"
            f"AGENT_NAME: {agent.name}\n"
            f"ROLE: {agent.role}\n"
            f"GOAL: {agent.goal}\n"
            f"TOOLS: {tools}\n"
            f"BACKSTORY: {agent.backstory}\n\n"
            f"TASK_NAME: {task.name}\n"
            f"TASK: {task.description}\n\n"
            f"EXPECTED_OUTPUT: {task.expected_output}\n"
        )

    def master_ai(self, high_level_goal: str) -> CrewResult:
        """
        Master SWARM AI orchestrates multi-agent collaboration to achieve a high-level goal.
        """
        if not self.llm.enabled():
            # Execute simulation mode logic early and prevent further processing
            return CrewResult(
                tasks=[Task(
                    name="Master Coordination",
                    description=f"Simulated coordination for goal: {high_level_goal}",
                    expected_output="Simulated output",
                    agent_name="MasterAI",
                )],
                outputs=[{
                    "task": "Master Coordination",
                    "result": f"[SIMULATED] Master AI simulated coordination for goal: {high_level_goal}",
                    "provider": "simulated",
                }]
            )

        # Define a high-level task for the Master AI
        master_task = Task(
            name="Master Coordination",
            description=f"Coordinate agents to achieve the goal: {high_level_goal}",
            expected_output="A detailed plan or result from all agents.",
            agent_name="MasterAI",
        )

        # Build a prompt for the Master AI
        prompt = (
            "You are the Master SWARM AI. Your role is to coordinate all agents to achieve the high-level goal.\n"
            f"HIGH_LEVEL_GOAL: {high_level_goal}\n"
            "AGENTS: " + ", ".join(self.agents.keys()) + "\n"
            "TASKS: " + ", ".join([task.name for task in self.tasks]) + "\n"
            "Provide a detailed plan or result."
        )

        try:
            # Generate a response using the OpenAI API
            response = self.llm.create_response(prompt)
            result_text = _extract_output_text(response)

            return CrewResult(
                tasks=[master_task],
                outputs=[{
                    "task": master_task.name,
                    "result": result_text,
                    "provider": "openai_responses",
                    "model": self.llm.model,
                }]
            )

        except Exception as e:
            return CrewResult(
                tasks=[master_task],
                outputs=[{
                    "task": master_task.name,
                    "error": str(e),
                    "provider": "openai_responses",
                    "model": self.llm.model,
                }]
            )


def crew_from_config(config: Dict[str, Any]) -> Crew:
    """
    Build a Crew from a JSON-like config.

    Shape:
    {
      "agents": [{...}],
      "tasks": [{...}],
      "verbose": true
    }
    """
    agents_cfg = config.get("agents", [])
    tasks_cfg = config.get("tasks", [])
    verbose = bool(config.get("verbose", True))

    agents: List[Agent] = []
    for a in agents_cfg:
        agents.append(
            Agent(
                name=a.get("name", "agent"),
                role=a.get("role", "Agent"),
                goal=a.get("goal", ""),
                backstory=a.get("backstory", ""),
                tools=a.get("tools") or [],
                verbose=bool(a.get("verbose", True)),
            )
        )

    tasks: List[Task] = []
    for t in tasks_cfg:
        tasks.append(
            Task(
                name=t.get("name", "task"),
                description=t.get("description", ""),
                expected_output=t.get("expected_output", ""),
                agent_name=t.get("agent_name", ""),
                async_execution=bool(t.get("async_execution", False)),
            )
        )

    return Crew(agents=agents, tasks=tasks, verbose=verbose)


