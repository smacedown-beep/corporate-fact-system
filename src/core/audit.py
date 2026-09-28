"""
Corporate Investment FACT System - Immutable Audit Logging Engine.
Records forensic, validation, acquisition, discovery, backtest, and approval events.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import json
from pathlib import Path

from src.core.hashing import compute_hashes

@dataclass
class AuditRecord:
    event_id: str
    timestamp: str
    event_type: str  # DATA_ACQUISITION, VALIDATION, BACKTEST, SECTOR_DISCOVERY, SECTOR_APPROVAL, QUARANTINE, HUMAN_APPROVAL
    user_or_action: str
    source: str
    object_id: str
    status: str
    hash_val: str
    reason: str
    metadata: Dict[str, Any]

class AuditLogEngine:
    """Manages appending and querying immutable system audit logs."""
    
    _instance = None
    
    def __init__(self, log_file: Optional[Path] = None):
        _PROJECT_ROOT = Path(__file__).resolve().parents[2]
        self.log_file = log_file or (_PROJECT_ROOT / "storage" / "system_audit_trail.jsonl")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.in_memory_logs: List[AuditRecord] = []
        self._load_existing()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AuditLogEngine()
        return cls._instance

    def _load_existing(self):
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            d = json.loads(line)
                            self.in_memory_logs.append(AuditRecord(**d))
            except Exception:
                pass

    def record_event(
        self,
        event_type: str,
        user_or_action: str,
        source: str,
        object_id: str,
        status: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
        data_to_hash: Optional[str] = None
    ) -> AuditRecord:
        now_iso = datetime.now(timezone.utc).isoformat()
        content_hash = compute_hashes(data_to_hash or f"{event_type}:{object_id}:{now_iso}")["sha256"]
        event_id = f"AUD_{now_iso[:10].replace('-','')}_{len(self.in_memory_logs)+1:05d}"
        
        record = AuditRecord(
            event_id=event_id,
            timestamp=now_iso,
            event_type=event_type,
            user_or_action=user_or_action,
            source=source,
            object_id=object_id,
            status=status,
            hash_val=content_hash,
            reason=reason,
            metadata=metadata or {}
        )
        self.in_memory_logs.append(record)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        return record

    def list_logs(self, event_type: Optional[str] = None, limit: int = 100) -> List[AuditRecord]:
        logs = self.in_memory_logs
        if event_type:
            logs = [l for l in logs if l.event_type == event_type]
        return logs[-limit:][::-1]
