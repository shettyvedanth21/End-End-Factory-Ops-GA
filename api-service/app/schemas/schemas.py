from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, time
from enum import Enum
import uuid

# --- Enums ---

class UserRole(str, Enum):
    PLATFORM_ROOT = "platform_root"
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"

class DeviceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ReportStatus(str, Enum):
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"

class ReportType(str, Enum):
    ENERGY = "energy"
    ALERTS = "alerts"
    ANALYTICS = "analytics"
    CUSTOM = "custom"
    
class AnalyticsMode(str, Enum):
    STANDARD = "standard"
    AI_COPILOT = "ai_copilot"

# --- Shared ---

class Pagination(BaseModel):
    page: int
    per_page: int
    total: int

class ResponseEnvelope(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Any] = None

# --- Auth ---

class LoginRequest(BaseModel):
    factory_slug: str
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: Any

class UserProfile(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    factory_id: Optional[str] = None
    can_write: bool
    last_login_at: Optional[datetime] = None

# --- Factory ---

class FactoryCreate(BaseModel):
    name: str
    slug: str
    timezone: str = "UTC"

class FactoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    timezone: str
    is_active: bool
    created_at: datetime
    
class FactoryAdminCreate(BaseModel):
    email: EmailStr
    password: str

# --- User ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole
    can_write: bool = False

class UserUpdate(BaseModel):
    can_write: Optional[bool] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    can_write: bool
    is_active: bool
    last_login_at: Optional[datetime]
    factory_id: Optional[str] = None

# --- Device ---

class DeviceCreate(BaseModel):
    id: str
    name: str
    type: str
    location: Optional[str] = None

class DeviceResponse(BaseModel):
    id: str
    factory_id: str
    name: str
    type: str
    location: Optional[str]
    status: DeviceStatus
    last_seen_at: Optional[datetime]
    created_at: datetime

class PropertyResponse(BaseModel):
    id: str
    property_name: str
    unit: Optional[str]
    data_type: str
    first_seen_at: datetime
    last_seen_at: datetime

# --- Telemetry ---

class TelemetryPoint(BaseModel):
    timestamp: datetime
    value: float

class TelemetryResponse(BaseModel):
    device_id: str
    property: str
    unit: Optional[str]
    aggregation: str
    window: str
    points: List[TelemetryPoint]

# --- Rule ---

class RuleCondition(BaseModel):
    property: str
    operator: str
    threshold: float

class RuleCreate(BaseModel):
    device_id: str
    name: str
    description: Optional[str] = None
    conditions: List[RuleCondition]
    condition_operator: str = "AND"
    schedule_start: Optional[str] = None # HH:MM:SS
    schedule_end: Optional[str] = None
    cooldown_seconds: int = 300
    auto_resolve: bool = False

class RuleUpdate(BaseModel):
    is_active: Optional[bool] = None
    cooldown_seconds: Optional[int] = None
    # Add other fields if needed

class RuleResponse(BaseModel):
    id: str
    factory_id: str
    device_id: str
    name: str
    is_active: bool
    conditions: List[RuleCondition] # Pydantic handles JSON to list conversion if structure matches
    condition_operator: str
    schedule_start: Optional[str]
    schedule_end: Optional[str]
    cooldown_seconds: int
    auto_resolve: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

# --- Alert ---

class AlertResponse(BaseModel):
    id: str
    rule_id: str
    device_id: str
    status: AlertStatus
    triggered_at: datetime
    trigger_values: Optional[Dict[str, Any]]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]

class AlertAcknowledge(BaseModel):
    notes: Optional[str]

class AlertResolve(BaseModel):
    notes: Optional[str]

# --- Analytics ---

class JobCreate(BaseModel):
    name: str
    mode: AnalyticsMode
    analysis_type: str
    device_ids: Optional[List[str]] = None
    properties: Optional[List[str]] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    model_name: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None

class JobResponse(BaseModel):
    id: str
    name: str
    mode: AnalyticsMode
    analysis_type: str
    status: JobStatus
    model_name: Optional[str]
    model_version: Optional[str]
    metrics: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    dataset_s3_key: Optional[str] = None
    artifact_s3_prefix: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None

class ModelResponse(BaseModel):
    id: str
    name: str
    version: str
    analysis_type: str
    source_job_id: str
    is_active: bool
    metrics: Optional[Dict[str, Any]]

# --- Reporting ---

class ReportCreate(BaseModel):
    name: str
    type: ReportType
    format: ReportFormat
    period_start: datetime
    period_end: datetime
    parameters: Optional[Dict[str, Any]] = None

class ReportResponse(BaseModel):
    id: str
    name: str
    status: ReportStatus
    format: ReportFormat
    download_url: Optional[str] = None
    download_expires_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None
