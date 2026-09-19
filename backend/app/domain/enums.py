"""Domain enums for analysis status, finding severities, and risk tiers."""

import enum


class JobStatus(enum.StrEnum):
    QUEUED = "QUEUED"
    CLONING = "CLONING"
    INDEXING = "INDEXING"
    STATIC_ANALYSIS = "STATIC_ANALYSIS"
    DEFECT_PREDICTION = "DEFECT_PREDICTION"
    AI_REVIEW = "AI_REVIEW"
    AGGREGATING = "AGGREGATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FindingSeverity(enum.StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingCategory(enum.StrEnum):
    SECURITY = "SECURITY"
    CODE_SMELL = "CODE_SMELL"
    BUG_RISK = "BUG_RISK"
    PERFORMANCE = "PERFORMANCE"
    MAINTAINABILITY = "MAINTAINABILITY"
    ARCHITECTURE = "ARCHITECTURE"


class RiskTier(enum.StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class CommentStatus(enum.StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DISMISSED = "DISMISSED"
