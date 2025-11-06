"""Pydantic schemas for specialized tools API."""

from __future__ import annotations

from datetime import date as Date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Ahkam Tool Schemas
# ============================================================================


class AhkamRequest(BaseModel):
    """Request schema for Ahkam ruling."""

    question: str = Field(..., min_length=10, max_length=500, description="Question to ask")
    marja_name: str = Field(default="Khamenei", description="Name of Marja")
    user_id: Optional[UUID] = Field(default=None, description="User ID for logging")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the ruling on working in a bank?",
                "marja_name": "Khamenei",
            }
        }


class AhkamResponse(BaseModel):
    """Response schema for Ahkam ruling."""

    question: str
    marja: str
    ruling: str
    source: str
    source_url: Optional[str] = None
    fetched_at: datetime
    from_cache: bool
    authenticity_note: str = Field(
        default="This ruling is fetched directly from official Marja source."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the ruling on working in a bank?",
                "marja": "Khamenei",
                "ruling": "Working in a conventional bank that deals with interest is not permissible...",
                "source": "Official Website",
                "source_url": "https://www.leader.ir/en/ahkam",
                "fetched_at": "2025-10-25T12:30:00Z",
                "from_cache": False,
                "authenticity_note": "This ruling is fetched directly from official Marja source.",
            }
        }


# ============================================================================
# Hadith Tool Schemas
# ============================================================================


class HadithSearchRequest(BaseModel):
    """Request schema for Hadith search."""

    query: str = Field(..., min_length=3, max_length=200, description="Search query")
    search_type: Literal["reference", "text", "narrator"] = Field(
        default="text", description="Type of search"
    )
    collection: Optional[str] = Field(
        default=None, description="Hadith collection (e.g., 'Sahih al-Kafi')"
    )
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "prayer",
                "search_type": "text",
                "collection": "Sahih al-Kafi",
                "limit": 10,
            }
        }


class HadithResult(BaseModel):
    """Single hadith result."""

    hadith_id: str
    collection: str
    reference: str
    text: str
    narrator_chain: list[str] = Field(default_factory=list)
    reliability: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "hadith_id": "123e4567-e89b-12d3-a456-426614174000",
                "collection": "Sahih al-Kafi",
                "reference": "al-Kafi 1:23",
                "text": "The Prophet (PBUH) said: Prayer is the pillar of religion...",
                "narrator_chain": ["Ali ibn Abi Talib", "Muhammad ibn Ya'qub"],
                "reliability": "sahih",
            }
        }


class HadithSearchResponse(BaseModel):
    """Response schema for Hadith search."""

    query: str
    search_type: str
    results: list[HadithResult]
    total_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "query": "prayer",
                "search_type": "text",
                "results": [],
                "total_count": 15,
            }
        }


# ============================================================================
# DateTime Tool Schemas
# ============================================================================


class PrayerTimesRequest(BaseModel):
    """Request schema for prayer times."""

    city: str = Field(..., min_length=2, max_length=100, description="City name")
    country: str = Field(..., min_length=2, max_length=100, description="Country name")
    request_date: Optional[Date] = Field(default=None, description="Date (defaults to today)", alias="date")

    class Config:
        json_schema_extra = {"example": {"city": "Tehran", "country": "Iran", "date": "2025-10-25"}}
        populate_by_name = True


class PrayerTimesResponse(BaseModel):
    """Response schema for prayer times."""

    city: str
    country: str
    prayer_date: Date
    prayer_times: dict[str, str]
    timezone: str
    calculation_method: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "city": "Tehran",
                "country": "Iran",
                "date": "2025-10-25",
                "prayer_times": {
                    "fajr": "05:30",
                    "sunrise": "07:00",
                    "dhuhr": "12:30",
                    "asr": "15:45",
                    "maghrib": "18:15",
                    "isha": "19:30",
                },
                "timezone": "Asia/Tehran",
                "calculation_method": "Institute of Geophysics, University of Tehran",
            }
        }


class DateConversionRequest(BaseModel):
    """Request schema for date conversion."""

    date: str = Field(..., description="Date to convert (YYYY-MM-DD or Hijri format)")
    from_calendar: Literal["gregorian", "hijri"] = Field(..., description="Source calendar")
    to_calendar: Literal["gregorian", "hijri"] = Field(..., description="Target calendar")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-10-25",
                "from_calendar": "gregorian",
                "to_calendar": "hijri",
            }
        }


class DateConversionResponse(BaseModel):
    """Response schema for date conversion."""

    original_date: str
    converted_date: str
    from_calendar: str
    to_calendar: str

    class Config:
        json_schema_extra = {
            "example": {
                "original_date": "2025-10-25",
                "converted_date": "1447-04-22",
                "from_calendar": "gregorian",
                "to_calendar": "hijri",
            }
        }


# ============================================================================
# Math Tool Schemas
# ============================================================================


class ZakatRequest(BaseModel):
    """Request schema for Zakat calculation."""

    total_wealth: float = Field(..., gt=0, description="Total wealth amount")
    currency: str = Field(default="USD", description="Currency code")

    class Config:
        json_schema_extra = {"example": {"total_wealth": 10000.0, "currency": "USD"}}


class ZakatResponse(BaseModel):
    """Response schema for Zakat calculation."""

    total_wealth: float
    zakat_amount: float
    nisab_threshold: float
    currency: str
    warning: str
    verification_required: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "total_wealth": 10000.0,
                "zakat_amount": 250.0,
                "nisab_threshold": 3500.0,
                "currency": "USD",
                "warning": "⚠️⚠️⚠️ CRITICAL WARNING ⚠️⚠️⚠️...",
                "verification_required": True,
            }
        }


class KhumsRequest(BaseModel):
    """Request schema for Khums calculation."""

    annual_income: float = Field(..., gt=0, description="Total annual income")
    annual_expenses: float = Field(..., ge=0, description="Total annual expenses")
    currency: str = Field(default="USD", description="Currency code")

    class Config:
        json_schema_extra = {
            "example": {"annual_income": 50000.0, "annual_expenses": 30000.0, "currency": "USD"}
        }


class KhumsResponse(BaseModel):
    """Response schema for Khums calculation."""

    annual_income: float
    annual_expenses: float
    net_savings: float
    khums_amount: float
    currency: str
    warning: str
    verification_required: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "annual_income": 50000.0,
                "annual_expenses": 30000.0,
                "net_savings": 20000.0,
                "khums_amount": 4000.0,
                "currency": "USD",
                "warning": "⚠️⚠️⚠️ CRITICAL WARNING ⚠️⚠️⚠️...",
                "verification_required": True,
            }
        }


# ============================================================================
# Multi-Tool Query Schemas
# ============================================================================


class MultiToolQueryRequest(BaseModel):
    """Request schema for multi-tool query."""

    query: str = Field(..., min_length=10, max_length=500, description="User query")
    user_context: Optional[dict] = Field(
        default_factory=dict,
        description="User context (marja_preference, city, country, etc.)",
    )
    execution_mode: Literal["parallel", "sequential"] = Field(
        default="parallel", description="Execution mode"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the ruling on zakat and when are prayer times in Tehran?",
                "user_context": {
                    "marja_preference": "Khamenei",
                    "city": "Tehran",
                    "country": "Iran",
                },
                "execution_mode": "parallel",
            }
        }


class MultiToolQueryResponse(BaseModel):
    """Response schema for multi-tool query."""

    query: str
    query_type: str
    tools_used: list[str]
    results: dict
    execution_summary: dict

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the ruling on zakat and when are prayer times in Tehran?",
                "query_type": "multi_tool",
                "tools_used": ["ahkam", "datetime"],
                "results": {
                    "ahkam": {"question": "...", "ruling": "..."},
                    "datetime": {"prayer_times": {"fajr": "05:30"}},
                },
                "execution_summary": {"total_tools": 2, "successful": 2, "failed": 0},
            }
        }
