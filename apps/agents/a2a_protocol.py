"""Lightweight Agent-to-Agent message envelope used by the engine."""
from dataclasses import dataclass, field, asdict
from typing import Optional, Any


@dataclass
class AgentMessageEnvelope:
    from_agent: str
    content: str
    message_type: str = 'update'
    priority: str = 'medium'
    to_agent: Optional[str] = None
    to_broadcast: bool = True
    raw_data: Optional[dict[str, Any]] = field(default=None)

    def to_dict(self) -> dict:
        return asdict(self)
