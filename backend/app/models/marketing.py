from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class Campaign(Base, TimestampMixin):
    """Marketing campaign entity."""

    __tablename__ = "campaigns"
    __table_args__ = (
        UniqueConstraint("organization_id", "campaign_code", name="uq_campaign_org_code"),
        CheckConstraint("budget_amount >= 0.00", name="ck_campaign_budget"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    target_segment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    budget_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    events: Mapped[list["CampaignEvent"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="campaign")


class CampaignEvent(Base):
    """Daily granular performance tracking for marketing campaigns."""

    __tablename__ = "campaign_events"
    __table_args__ = (
        UniqueConstraint("campaign_id", "date", name="uq_campaign_event_date"),
        CheckConstraint("spend >= 0.00", name="ck_campaign_event_spend"),
        CheckConstraint("impressions >= 0", name="ck_campaign_event_impressions"),
        CheckConstraint("clicks >= 0", name="ck_campaign_event_clicks"),
        CheckConstraint("conversions >= 0", name="ck_campaign_event_conversions"),
        CheckConstraint("attributed_revenue >= 0.00", name="ck_campaign_event_attributed_rev"),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    spend: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0.00, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attributed_revenue: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=0.00, nullable=False
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="events")
