from pydantic import BaseModel
from typing import List, Optional

# ... (Draft/Inbox schemas unchanged) ...
class DraftSummary(BaseModel):
    draft_id: int
    subject: str
    status: str
    class Config:
        from_attributes = True

class DraftDetail(BaseModel):
    draft_id: int
    status: str
    generated_text: str
    original_sender: str
    original_subject: str
    original_body: str
    is_read_and_confirmed: bool
    correspondent_tone: Optional[str] = None
    correspondent_goal: Optional[str] = None
    correspondent_evidence: Optional[str] = None
    class Config:
        from_attributes = True

class DraftEditRequest(BaseModel):
    final_text: str

class DraftRewriteRequest(BaseModel):
    paragraph: str
    goal: str
    tone: str
    tone_dial_value: float
    ad_hoc_instruction: str
    model: str

class InboxItem(BaseModel):
    email_id: int
    correspondent: str
    subject: str
    has_draft: bool
    draft_id: Optional[int] = None
    draft_status: Optional[str] = None
    local_priority_score: float = 0.0

# --- MODIFIED: Group Schemas ---
class GroupBase(BaseModel):
    name: str
    group_goal: Optional[str] = None
    group_tone: Optional[str] = None
    group_urgency: Optional[float] = None
    color: Optional[str] = "#ffffff" # <-- NEW

class GroupCreate(GroupBase):
    pass

class GroupDetail(GroupBase):
    id: int
    class Config:
        from_attributes = True

# --- Contact Schemas ---
class ContactBase(BaseModel):
    email_address: str
    name: Optional[str] = None
    group_id: Optional[int] = None
    contact_group: Optional[str] = None
    tone: Optional[str] = None
    tone_strength: Optional[float] = None
    goal: Optional[str] = None
    auto_draft_enabled: Optional[bool] = True

class ContactCreate(ContactBase):
    pass

class ContactDetail(ContactBase):
    id: int
    group: Optional[GroupDetail] = None
    class Config:
        from_attributes = True

# ... (Settings & Model schemas unchanged) ...
class SettingsItem(BaseModel):
    key: str
    value: str

class SettingsUpdateRequest(BaseModel):
    settings: List[SettingsItem]

class GenerationRequest(BaseModel):
    input_text: str
    model_name: str
    goal: str
    tone: str
    tone_dial_value: float = 0.5
    ad_hoc_instruction: str = ""

class ModelItem(BaseModel):
    name: str
    is_installed: bool
    is_selected: bool
    status_color: str

class ModelSettingRequest(BaseModel):
    model_name: str