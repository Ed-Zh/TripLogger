from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Any, Optional
import uuid

@dataclass
class Trip:
    start_date: str  # Format: YYYY-MM-DD or YYYY-MM
    end_date: str    # Format: YYYY-MM-DD or YYYY-MM
    city: str
    country: str
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "city": self.city,
            "country": self.country,
            "notes": self.notes,
            "tags": self.tags,
            "attachments": self.attachments
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trip':
        return cls(
            id=data["id"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            city=data["city"],
            country=data["country"],
            notes=data.get("notes", ""),
            tags=data.get("tags", []),
            attachments=data.get("attachments", [])
        )
