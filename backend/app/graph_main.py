"""
graph_main.py — Standalone graph runner for testing without FastAPI.

Usage:
    python graph_main.py                                # interactive HITL
    AUTO_APPROVE=true python graph_main.py              # skip HITL prompt
    SESSION_ID=my-test python graph_main.py             # named session
    PROMPT="Migrate app=svc from eu-west-1 to ap-south-1" python graph_main.py

Output: sessions/<session_id>.tf
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphInterrupt
from langgraph.types import Command

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("graph_main")

DEFAULT_PROMPT = (
    "Migrate all AWS resources tagged app=n8n-csp-host "
    "from ap-south-1 to us-east-1 using terraform."
)
PROMPT = os.getenv("PROMPT", DEFAULT_PROMPT)
SESSION_ID = os.getenv("SESSION_ID", f"test-{uuid.uuid4().hex[:8]}")
AUTO_APPROVE = os.getenv("AUTO_APPROVE", "false").lower() == "true"


def _sep(label: str = "") -> None:
    w = 64
    if label:
        pad = max(0, (w - len(label) - 2) // 2)
        print(f"\n{'─' * pad} {label} {'─' * pad}")
    else:
        print("─" * w)


async def run() -> None:
    from app.graph.builder import migration_graph

    config: RunnableConfig = {"configurable": {"thread_id": SESSION_ID}}
    input_payload: dict | Command = {
        "user_prompt": PROMPT,
        "session_id": SESSION_ID,
        "errors": [],
        "discovered_resources": [],
        "ordered_resources": [],
    }

    _sep("AWS Migration Agent — Standalone Test Runner")
    print(f"  Session    : {SESSION_ID}")
    print(f"  Prompt     : {PROMPT}")
    print(f"  AWS creds  : {'✅ found' if os.getenv('AWS_ACCESS_KEY_ID') else '⚠️  not found — using MOCK data'}")
    print(f"  Auto-approve HITL : {AUTO_APPROVE}")
    _sep()

    hitl_count = 0

    while True:
        try:
            async for chunk in migration_graph.astream(
                input_payload,
                config=config,
                stream_mode="updates",
            ):
                for node_name, delta in chunk.items():
                    _sep(node_name)
                    print(f"  Step   : {delta.get('current_step', node_name)}")
                    errors = delta.get("errors", [])
                    if errors:
                        print(f"  Errors : {errors}")
                    if "migration_request" in delta and delta["migration_request"]:
                        req = delta["migration_request"]
                        print(f"  Parsed : {req.tag_key}={req.tag_value} | {req.source_region} → {req.target_region} | {req.iac_format}")
                    if "discovered_resources" in delta:
                        print(f"  Resources found : {len(delta['discovered_resources'])}")
                    if "ordered_resources" in delta:
                        print(f"  Ordered : {[r.resource_id for r in delta['ordered_resources']]}")
                    if "generated_iac" in delta:
                        path = delta.get("iac_file_path", "")
                        iac = delta["generated_iac"]
                        print(f"\n  📄 IaC file : {path}")
                        print(f"\n--- Preview (first 600 chars) ---")
                        print(iac[:600])
                        if len(iac) > 600:
                            print(f"... ({len(iac)} chars total)")

            _sep("DONE ✅")
            print("  Migration pipeline completed successfully.")
            break

        except GraphInterrupt as exc:
            hitl_count += 1
            payload = exc.args[0] if exc.args else {}
            _sep(f"⏸  HITL GATE (loop #{hitl_count})")
            print(f"  IaC file : {payload.get('iac_file_path', 'N/A')}")
            print(f"  Resources: {payload.get('resource_count', 0)}")

            if AUTO_APPROVE:
                decision, feedback = "approve", ""
                print("  AUTO_APPROVE=true → approving automatically")
            else:
                print("\n  [a] Approve   [r] Reject with feedback   [q] Quit")
                choice = input("  Choice: ").strip().lower()
                if choice == "q":
                    print("  Exiting.")
                    return
                elif choice == "r":
                    feedback = input("  Feedback for IaC generator: ").strip()
                    decision = "reject"
                else:
                    decision, feedback = "approve", ""

            if hitl_count >= 3 and decision == "reject":
                print("  ⚠️  Max HITL loops reached — forcing approve")
                decision, feedback = "approve", ""

            input_payload = Command(resume={"decision": decision, "feedback": feedback})
            print(f"  Resuming with decision='{decision}'")

        except Exception as exc:
            _sep("ERROR ❌")
            logger.exception("Graph run failed")
            break

    # Final state snapshot
    try:
        snap = await migration_graph.aget_state(config)
        vals = snap.values
        _sep("Final State")
        print(f"  current_step    : {vals.get('current_step')}")
        print(f"  iac_file_path   : {vals.get('iac_file_path')}")
        print(f"  resources found : {len(vals.get('discovered_resources', []))}")
        print(f"  errors          : {vals.get('errors', [])}")
    except Exception as exc:
        logger.warning("Could not fetch final state: %s", exc)

    _sep()


if __name__ == "__main__":
    asyncio.run(run())