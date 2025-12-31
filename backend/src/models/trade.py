"""Trade models for construction takeoffs."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class TradeType(str, Enum):
    """Supported construction trades."""
    PAINTING = "painting"
    DRYWALL = "drywall"
    DOORS_WINDOWS = "doors_windows"
    FLOORING = "flooring"
    CONCRETE = "concrete"
    ROOFING = "roofing"
    HVAC = "hvac"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    EARTHWORK = "earthwork"
    LANDSCAPING = "landscaping"


class TradeConfig(BaseModel):
    """Configuration for a trade."""
    trade_type: TradeType
    enabled: bool = True
    extraction_params: Dict = {}
    validation_rules: Dict = {}
    unit_of_measure: str = "count"
    
    class Config:
        use_enum_values = True


class TradeExtractionResult(BaseModel):
    """Result of trade-specific extraction."""
    trade_type: TradeType
    quantities: Dict[str, Any]
    confidence: float
    units: Dict[str, str]
    metadata: Dict = {}
    
    class Config:
        use_enum_values = True


# Trade-specific extraction configurations
TRADE_CONFIGS: Dict[TradeType, TradeConfig] = {
    TradeType.PAINTING: TradeConfig(
        trade_type=TradeType.PAINTING,
        unit_of_measure="sqft",
        extraction_params={
            "extract_walls": True,
            "extract_ceiling": True,
            "extract_trim": True,
            "extract_exterior": True
        },
        validation_rules={
            "min_area": 0,
            "max_area_per_room": 10000,
            "typical_coverage": 350  # sqft per gallon
        }
    ),
    TradeType.DRYWALL: TradeConfig(
        trade_type=TradeType.DRYWALL,
        unit_of_measure="sheets",
        extraction_params={
            "sheet_size": "4x8",
            "extract_linear_feet": True
        },
        validation_rules={
            "min_sheets": 0,
            "max_sheets_per_room": 100
        }
    ),
    TradeType.DOORS_WINDOWS: TradeConfig(
        trade_type=TradeType.DOORS_WINDOWS,
        unit_of_measure="count",
        extraction_params={
            "extract_doors": True,
            "extract_windows": True,
            "extract_hardware": True,
            "extract_sizes": True
        },
        validation_rules={
            "min_doors": 0,
            "max_doors_per_floor": 500,
            "min_windows": 0,
            "max_windows_per_floor": 1000
        }
    ),
    TradeType.FLOORING: TradeConfig(
        trade_type=TradeType.FLOORING,
        unit_of_measure="sqft",
        extraction_params={
            "extract_by_type": True,
            "extract_room_wise": True
        },
        validation_rules={
            "min_area": 0,
            "max_area_per_room": 5000
        }
    ),
    TradeType.CONCRETE: TradeConfig(
        trade_type=TradeType.CONCRETE,
        unit_of_measure="cubic_yards",
        extraction_params={
            "extract_slabs": True,
            "extract_foundations": True,
            "extract_walls": True
        },
        validation_rules={
            "min_volume": 0,
            "max_volume_per_project": 10000
        }
    ),
}

