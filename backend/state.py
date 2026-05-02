from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class MineState:
    mill_grinding_active: bool = True
    mill_flotation_active: bool = True
    haulage_active: bool = True
    drilling_active: bool = True
    ore_stockpile_tons: float = 12000.0
    processed_today_tons: float = 0.0
    energy_mode: str = "normal"  # normal | reduced | minimal
    target_commodity: str = "gold"  # gold | copper | silver
    shift_schedule: str = "full"  # full | reduced | skeleton
    notes: str = ""
    updated_at: datetime = field(default_factory=datetime.utcnow)


# Singleton mine state shared across agents
mine_state = MineState()
