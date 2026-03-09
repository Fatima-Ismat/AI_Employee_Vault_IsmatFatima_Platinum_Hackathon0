"""
Agent-to-Agent (A2A) Communication Protocol
─────────────────────────────────────────────
Enables multiple AI agents to exchange structured messages via JSON files
stored in a shared message bus directory.

Use cases:
  • Cloud agent delegates sensitive task to local agent
  • Local agent requests supplementary research from cloud agent
  • Coordinator agent routes tasks to specialized sub-agents
  • Agents broadcast status updates to orchestrator

Message bus: agents/messages/

Protocol:
  - Each message is a JSON file: msg_<uuid>.json
  - Messages have: from, to, type, payload, timestamp, status
  - Receiver polls bus directory and processes messages addressed to it
  - Processed messages moved to agents/messages/processed/
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.logger import get_logger

log = get_logger("agents.a2a")

MESSAGE_BUS_DIR   = Path(__file__).parent / "messages"
PROCESSED_DIR     = MESSAGE_BUS_DIR / "processed"
DEAD_LETTER_DIR   = MESSAGE_BUS_DIR / "dead_letter"

# ── Message Types ─────────────────────────────────────────────────────────────
MSG_DELEGATE    = "delegate"       # Delegate task to another agent
MSG_RESULT      = "result"         # Return result of a delegated task
MSG_STATUS      = "status"         # Agent status broadcast
MSG_QUERY       = "query"          # Request information
MSG_RESPONSE    = "response"       # Response to a query
MSG_HEARTBEAT   = "heartbeat"      # Liveness signal


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dirs() -> None:
    for d in (MESSAGE_BUS_DIR, PROCESSED_DIR, DEAD_LETTER_DIR):
        d.mkdir(parents=True, exist_ok=True)


# ── Message Construction ───────────────────────────────────────────────────────

def create_message(
    from_agent:  str,
    to_agent:    str,
    msg_type:    str,
    payload:     dict,
    reply_to:    Optional[str] = None,
    priority:    str = "MEDIUM",
) -> dict:
    """Build a structured A2A message dict."""
    return {
        "message_id": str(uuid.uuid4())[:12],
        "from":       from_agent,
        "to":         to_agent,
        "type":       msg_type,
        "payload":    payload,
        "reply_to":   reply_to,
        "priority":   priority,
        "timestamp":  _now(),
        "status":     "pending",
    }


def send_message(message: dict) -> Path:
    """Write a message to the shared message bus. Returns message file path."""
    _ensure_dirs()
    msg_id   = message["message_id"]
    msg_path = MESSAGE_BUS_DIR / f"msg_{msg_id}.json"
    msg_path.write_text(json.dumps(message, indent=2), encoding="utf-8")
    log.info(f"[A2A] Sent: {message['type']} from={message['from']} to={message['to']} id={msg_id}")
    return msg_path


def send_delegation(
    from_agent: str,
    to_agent:   str,
    task_id:    str,
    plan:       dict,
    reason:     str = "",
) -> Path:
    """Shortcut: send a task delegation message."""
    msg = create_message(
        from_agent=from_agent,
        to_agent=to_agent,
        msg_type=MSG_DELEGATE,
        payload={"task_id": task_id, "plan": plan, "reason": reason},
        priority=plan.get("priority", "MEDIUM"),
    )
    return send_message(msg)


def send_result(
    from_agent:  str,
    to_agent:    str,
    task_id:     str,
    status:      str,
    summary:     str,
    reply_to:    Optional[str] = None,
) -> Path:
    """Shortcut: send a task completion result."""
    msg = create_message(
        from_agent=from_agent,
        to_agent=to_agent,
        msg_type=MSG_RESULT,
        payload={"task_id": task_id, "status": status, "summary": summary},
        reply_to=reply_to,
    )
    return send_message(msg)


def send_heartbeat(agent_id: str, status: str = "running", metadata: dict = None) -> Path:
    """Broadcast a heartbeat to all agents (to=broadcast)."""
    msg = create_message(
        from_agent=agent_id,
        to_agent="broadcast",
        msg_type=MSG_HEARTBEAT,
        payload={"status": status, "metadata": metadata or {}},
    )
    return send_message(msg)


# ── Message Receiver ──────────────────────────────────────────────────────────

class A2AReceiver:
    """
    Poll the message bus and process messages addressed to this agent.

    Usage:
        receiver = A2AReceiver("local-agent")
        receiver.register_handler("delegate", handle_delegation)
        receiver.poll_once()
    """

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self._handlers: dict[str, Callable] = {}
        _ensure_dirs()

    def register_handler(self, msg_type: str, handler: Callable[[dict], Any]) -> None:
        """Register a callable to handle a specific message type."""
        self._handlers[msg_type] = handler
        log.debug(f"[A2A] Handler registered: {msg_type} → {handler.__name__}")

    def poll_once(self) -> list[dict]:
        """Process all pending messages addressed to this agent. Returns list of processed."""
        processed = []
        for msg_file in sorted(MESSAGE_BUS_DIR.glob("msg_*.json")):
            try:
                msg = json.loads(msg_file.read_text(encoding="utf-8"))
                to = msg.get("to", "")
                if to not in (self.agent_id, "broadcast"):
                    continue

                msg_type = msg.get("type", "")
                handler  = self._handlers.get(msg_type)

                if handler:
                    log.info(f"[A2A] Processing: {msg_type} from={msg['from']} id={msg['message_id']}")
                    try:
                        handler(msg)
                        msg["status"] = "processed"
                    except Exception as e:
                        log.error(f"[A2A] Handler error for {msg_type}: {e}")
                        msg["status"] = "error"
                        self._move_to_dead_letter(msg_file, msg)
                        continue
                else:
                    log.warning(f"[A2A] No handler for type: {msg_type}")
                    msg["status"] = "no_handler"

                # Move to processed
                dest = PROCESSED_DIR / msg_file.name
                dest.write_text(json.dumps(msg, indent=2), encoding="utf-8")
                msg_file.unlink()
                processed.append(msg)

            except Exception as e:
                log.error(f"[A2A] Failed to read message {msg_file.name}: {e}")

        return processed

    def _move_to_dead_letter(self, msg_file: Path, msg: dict) -> None:
        dest = DEAD_LETTER_DIR / msg_file.name
        dest.write_text(json.dumps(msg, indent=2), encoding="utf-8")
        msg_file.unlink(missing_ok=True)
        log.error(f"[A2A] Dead-lettered: {msg_file.name}")

    def get_message_stats(self) -> dict:
        """Return counts of pending, processed, and dead-letter messages."""
        return {
            "pending":     len(list(MESSAGE_BUS_DIR.glob("msg_*.json"))),
            "processed":   len(list(PROCESSED_DIR.glob("msg_*.json"))),
            "dead_letter": len(list(DEAD_LETTER_DIR.glob("msg_*.json"))),
        }


# ── Example Usage ─────────────────────────────────────────────────────────────

def _demo_handler(msg: dict) -> None:
    print(f"[Demo handler] Received: {msg['type']} from {msg['from']}")
    print(f"  Payload: {msg['payload']}")


if __name__ == "__main__":
    # Demo: send a delegation message and receive it
    print("A2A Protocol Demo")

    # Agent 1 (cloud) sends delegation to Agent 2 (local)
    send_delegation(
        from_agent="cloud-agent-01",
        to_agent="local-agent",
        task_id="task_demo_abc",
        plan={"summary": "Send reply email", "tools_required": ["email_mcp"],
              "requires_approval": True, "draft_action": "Dear client..."},
        reason="Sensitive action requires local HITL",
    )
    print("Message sent to bus")

    # Agent 2 (local) polls and processes
    receiver = A2AReceiver("local-agent")
    receiver.register_handler(MSG_DELEGATE, _demo_handler)
    processed = receiver.poll_once()
    print(f"Processed {len(processed)} message(s)")
    print(f"Stats: {receiver.get_message_stats()}")
