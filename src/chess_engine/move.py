from dataclasses import dataclass

@dataclass(frozen=True)
class Move():
    from_sq: int
    to_sq: int
    promotion: str | None = None