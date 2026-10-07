"""Audit logging for the AI Simplified Lab production system.

Every controller mutation, stage transition, approval, rejection, or error creates an
immutable, chronological audit event stored in projects/<production_id>/audit_log.jsonl.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field

from schemas.models.common import Severity


class AuditEvent(BaseModel):
    """An immutable record of an event or action during production."""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    production_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str             # e.g. "production_created", "stage_started", "stage_completed", ...
    stage: str | None = None
    actor: str = "system"       # "system", "human", "llm", "tool"
    severity: Severity = Severity.INFO
    details: dict[str, Any] = Field(default_factory=dict)
    message: str = ""

    model_config = {"extra": "forbid"}

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "AuditEvent":
        return cls.model_validate_json(json_str)


class AuditLog:
    """Manages the append-only audit log for a single production run."""

    def __init__(self, project_dir: Path, production_id: str) -> None:
        self.project_dir = Path(project_dir)
        self.production_id = production_id
        self.log_path = self.project_dir / "audit_log.jsonl"

    def record(
        self,
        event_type: str,
        stage: str | None = None,
        actor: str = "system",
        severity: Severity = Severity.INFO,
        details: dict[str, Any] | None = None,
        message: str = "",
    ) -> AuditEvent:
        """Create, persist, and return an audit event."""
        self.project_dir.mkdir(parents=True, exist_ok=True)
        event = AuditEvent(
            production_id=self.production_id,
            event_type=event_type,
            stage=stage,
            actor=actor,
            severity=severity,
            details=details or {},
            message=message,
        )
        line = event.to_json() + "\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
        return event

    def list_events(
        self,
        stage: str | None = None,
        event_type: str | None = None,
    ) -> list[AuditEvent]:
        """Read and filter audit events."""
        if not self.log_path.exists():
            return []
        events: list[AuditEvent] = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = AuditEvent.from_json(line)
                    if stage is not None and ev.stage != stage:
                        continue
                    if event_type is not None and ev.event_type != event_type:
                        continue
                    events.append(ev)
                except Exception:
                    continue
        return events
