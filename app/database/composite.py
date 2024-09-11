from dataclasses import dataclass
from sqlalchemy.ext.mutable import MutableComposite


@dataclass
class Name(MutableComposite):
    first: str
    middle: str | None
    last: str

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        self.changed()
    
    def __str__(self) -> str:
        mid = f" {self.middle}" if self.middle else ""
        return f"{self.first}{mid} {self.last}"
    
    def __repr__(self) -> str:
        mid = f", middle='{self.middle}'" if self.middle else ""
        return f"Name(first='{self.first}'{mid}, last='{self.last}')"
