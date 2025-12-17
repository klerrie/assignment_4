"""
Pydantic models for contract change extraction output validation.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ContractChangeOutput(BaseModel):
    """
    Structured output model for contract change extraction.
    Validates and ensures data integrity for downstream systems.
    """
    sections_changed: List[str] = Field(
        ...,
        description="List of section names or identifiers that were modified",
        min_length=1,
        examples=["Section 3: Payment Terms", "Section 7: Termination Clause"]
    )
    
    topics_touched: List[str] = Field(
        ...,
        description="List of topics or subject areas affected by the changes",
        min_length=1,
        examples=["Payment Schedule", "Liability", "Intellectual Property"]
    )
    
    summary_of_the_change: str = Field(
        ...,
        description="A comprehensive summary of all changes introduced in the amendment",
        min_length=50,
        examples=["The payment terms were extended from 30 to 45 days, and a new termination clause was added allowing either party to terminate with 60 days notice."
        ]
    )
    
    @field_validator('sections_changed')
    @classmethod
    def validate_sections_changed(cls, v: List[str]) -> List[str]:
        """Ensure sections_changed contains non-empty strings."""
        if not v:
            raise ValueError("sections_changed must contain at least one section")
        for section in v:
            if not section.strip():
                raise ValueError("Each section name must be non-empty")
        return [s.strip() for s in v]
    
    @field_validator('topics_touched')
    @classmethod
    def validate_topics_touched(cls, v: List[str]) -> List[str]:
        """Ensure topics_touched contains non-empty strings."""
        if not v:
            raise ValueError("topics_touched must contain at least one topic")
        for topic in v:
            if not topic.strip():
                raise ValueError("Each topic must be non-empty")
        return [t.strip() for t in v]
    
    @field_validator('summary_of_the_change')
    @classmethod
    def validate_summary(cls, v: str) -> str:
        """Ensure summary is meaningful and not too short."""
        if len(v.strip()) < 50:
            raise ValueError("summary_of_the_change must be at least 50 characters long")
        return v.strip()
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sections_changed": [
                    "Section 3: Payment Terms",
                    "Section 7: Termination Clause"
                ],
                "topics_touched": [
                    "Payment Schedule",
                    "Liability",
                    "Termination Rights"
                ],
                "summary_of_the_change": "The payment terms were extended from 30 to 45 days, and a new termination clause was added allowing either party to terminate with 60 days notice."
            }
        }
    )
