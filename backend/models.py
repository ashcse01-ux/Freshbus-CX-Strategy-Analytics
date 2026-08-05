from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import MasterBase, TenantBase

class UploadManifest(TenantBase):
    __tablename__ = "upload_manifests"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    call_date = Column(String)
    gross_tickets = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CallRecord(TenantBase):
    __tablename__ = "call_records"
    id = Column(Integer, primary_key=True, index=True)
    
    # Unique identifier to prevent double counting
    row_hash = Column(String, unique=True, index=True)
    
    Call_ID = Column(String, index=True)
    Call_Type = Column(String)
    Campaign = Column(String, index=True)
    Location = Column(String)
    Caller_No = Column(String)
    Caller_E164 = Column(String)
    Skill = Column(String)
    Call_Date = Column(String, index=True)
    Queue_Time = Column(String)
    Start_Time = Column(String)
    Time_to_Answer = Column(String)
    End_Time = Column(String)
    Talk_Time = Column(String)
    Hold_Time = Column(String)
    Duration = Column(String)
    Call_Flow = Column(String)
    Dialed_Number = Column(String)
    Agent = Column(String, index=True)
    Disposition = Column(String, index=True)
    Wrapup_Duration = Column(String)
    Handling_Time = Column(String)
    Status = Column(String, index=True)
    Dial_Status = Column(String)
    Customer_Dial_Status = Column(String)
    Agent_Dial_Status = Column(String)
    Hangup_By = Column(String, index=True)
    Transfer_Details = Column(String)
    UUI = Column(String)
    Comments = Column(String)
    Feedback = Column(String)
    Customer_Ring_Time = Column(String)
    Recording_URL = Column(String)
    Agent_ID = Column(String)
    Ratings = Column(String)
    Rating_Comments = Column(String)
    DynamicDid = Column(String)
    DID = Column(String, index=True)

class DailyManualMetric(TenantBase):
    """One row per date — stores all manual/operational metrics from the Excel sheet."""
    __tablename__ = "daily_manual_metrics"
    id              = Column(Integer, primary_key=True, index=True)
    date            = Column(String, unique=True, index=True)   # YYYY-MM-DD

    # Business volume
    gross_seats     = Column(Float)
    gross_tickets   = Column(Float)

    # Journey interaction
    intr_journey_overall    = Column(Float)   # ratio  e.g. 0.0531
    intr_journey_inbound_wh = Column(Float)   # ratio
    intr_journey_travel     = Column(Float)   # ratio

    # Quality
    defects         = Column(Float)
    defects_journey = Column(Float)

    # Headcount
    present_agent_hc = Column(Integer)

    # Service disruptions — counts
    service_delay_count     = Column(Integer)
    service_cancel_count    = Column(Integer)
    service_breakdown_count = Column(Integer)

    # Service disruptions — pax impacted
    delay_pax_impacted     = Column(Integer)
    cancel_pax_impacted    = Column(Integer)
    breakdown_pax_impacted = Column(Integer)
    total_pax_impacted     = Column(Integer)

    # Impact percentages
    impacted_pct             = Column(Float)   # decimal e.g. 0.0435
    cancellations_impact_pct = Column(Float)   # decimal

    # New Inbound Metrics
    call_drop_not_done       = Column(Integer)
    blank_call_not_done      = Column(Integer)
    overall_call_not_done    = Column(Integer)
    call_not_done_pct        = Column(Float)
    agent_disconnected       = Column(Integer)
    agent_disconnected_pct   = Column(Float)
    call_not_disposed        = Column(Integer)
    call_not_disposed_pct    = Column(Float)


class ProcessedSync(TenantBase):
    __tablename__ = "processed_syncs"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True) # Google Drive File ID
    filename = Column(String)
    record_count = Column(Integer)
    synced_at = Column(DateTime(timezone=True), server_default=func.now())

class CampaignGroup(MasterBase):
    __tablename__ = "campaign_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    icon = Column(String, default="phone-incoming")
    status = Column(String, default="Live")
    
    # Relationships
    sub_campaigns = relationship("SubCampaign", back_populates="parent", cascade="all, delete-orphan")

class SubCampaign(MasterBase):
    __tablename__ = "sub_campaigns"
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("campaign_groups.id"))
    ozonetel_name = Column(String, index=True)
    
    # Relationships
    parent = relationship("CampaignGroup", back_populates="sub_campaigns")
