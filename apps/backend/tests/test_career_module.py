# apps/backend/tests/test_career_module.py
"""Unit tests untuk Upwork Career Engine:
- Target pendapatan bulanan ($ USD & konversi IDR) dengan progress bar
- Pipeline pengajuan proposal (submitted -> interviewing -> hired -> rejected)
- Pemantauan Connects dan conversion rate
- Manajemen kontrak kerja aktif, penambahan earning, dan penyelesaian kontrak
- Bot command handlers (/karir, /proposal, /kontrak) dan interactive callbacks (career:*)
"""

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys
import uuid
from zoneinfo import ZoneInfo

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("GOOGLE_API_KEY", "test_key")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import (
    CareerGoal,
    Profile,
    UpworkContract,
    UpworkProposal,
    utcnow,
)
from app.career import (
    add_contract_earnings,
    add_upwork_contract,
    add_upwork_proposal,
    build_career_dashboard_keyboard,
    build_contracts_list_keyboard,
    build_proposals_list_keyboard,
    complete_upwork_contract,
    cycle_proposal_status,
    format_career_dashboard_html,
    format_contracts_list_html,
    format_proposals_list_html,
    get_active_contracts,
    get_all_contracts,
    get_career_summary,
    get_current_month_str,
    get_or_create_monthly_career_goal,
    get_recent_proposals,
    render_progress_bar,
    update_career_goal,
    update_proposal_status,
)
import app.bot as bot_module


class MockCallbackQuery:
    def __init__(self, data: str, chat_id: int):
        self.data = data
        self.message = MockMessage()
        self.answered = False
        self.answer_text = None
        self.edited_text = None
        self.reply_markup = None

    async def answer(self, text: str = None, show_alert: bool = False):
        self.answered = True
        self.answer_text = text

    async def edit_message_text(self, text: str, **kwargs):
        self.edited_text = text
        if "reply_markup" in kwargs:
            self.reply_markup = kwargs["reply_markup"]


class MockMessage:
    def __init__(self):
        self.replies = []
        self.reply_markups = []

    async def reply_text(self, text: str, *args, **kwargs):
        self.replies.append(text)
        if "reply_markup" in kwargs:
            self.reply_markups.append(kwargs["reply_markup"])


class MockUpdate:
    def __init__(self, chat_id: int, text: str = "", callback_data: str = None):
        self.effective_chat = type("Chat", (), {"id": chat_id})()
        self.effective_message = MockMessage()
        self.callback_query = (
            MockCallbackQuery(callback_data, chat_id) if callback_data else None
        )


class MockContext:
    def __init__(self, args: list = None):
        self.args = args or []


@pytest_asyncio.fixture
async def setup_test_db():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    TestSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    bot_module.SessionLocal = TestSessionLocal

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    user_id = uuid.uuid4()
    chat_id = 99912345

    async with TestSessionLocal() as session:
        profile = Profile(
            id=user_id,
            email="freelancer@upwork.com",
            full_name="Frans Freelancer",
            telegram_chat_id=chat_id,
        )
        session.add(profile)
        await session.commit()

    yield {"user_id": user_id, "chat_id": chat_id, "session_factory": TestSessionLocal}
    await test_engine.dispose()


# ============================================================================
# 1. TEST CAREER GOALS & TARGETS
# ============================================================================

@pytest.mark.asyncio
async def test_career_goal_flow(setup_test_db):
    user_id = setup_test_db["user_id"]
    session_factory = setup_test_db["session_factory"]

    async with session_factory() as session:
        # Default creation
        goal = await get_or_create_monthly_career_goal(session, user_id)
        assert goal is not None
        assert goal.user_id == user_id
        assert goal.target_revenue_usd == 1000.0
        assert goal.target_proposals_count == 20
        assert goal.current_badge == "Rising Talent"
        assert goal.usd_to_idr_rate == 16200.0

        # Update goal
        updated = await update_career_goal(
            session=session,
            user_id=user_id,
            target_revenue_usd=1500.0,
            target_proposals_count=25,
            current_badge="Top Rated",
            usd_to_idr_rate=16500.0,
        )
        assert updated.target_revenue_usd == 1500.0
        assert updated.target_proposals_count == 25
        assert updated.current_badge == "Top Rated"
        assert updated.usd_to_idr_rate == 16500.0

        # Re-fetch should yield updated values
        refetched = await get_or_create_monthly_career_goal(session, user_id)
        assert refetched.target_revenue_usd == 1500.0


# ============================================================================
# 2. TEST PROPOSAL PIPELINE & CONNECTS
# ============================================================================

@pytest.mark.asyncio
async def test_proposal_pipeline_flow(setup_test_db):
    user_id = setup_test_db["user_id"]
    session_factory = setup_test_db["session_factory"]

    async with session_factory() as session:
        # 1. Add proposals
        prop1 = await add_upwork_proposal(
            session=session,
            user_id=user_id,
            job_title="Build AI Agent in Python",
            bid_amount_usd=400.0,
            connects_spent=8,
            client_country="United States",
            notes="Fast delivery promised",
        )
        assert prop1.id is not None
        assert prop1.status == "submitted"
        assert prop1.connects_spent == 8

        prop2 = await add_upwork_proposal(
            session=session,
            user_id=user_id,
            job_title="Scrape E-Commerce Data",
            bid_amount_usd=150.0,
            connects_spent=6,
            client_country="Germany",
        )

        # 2. Get recent proposals
        props = await get_recent_proposals(session, user_id, limit=10)
        assert len(props) == 2

        # 3. Update status directly
        updated = await update_proposal_status(session, user_id, prop1.id, "interviewing")
        assert updated is not None
        assert updated.status == "interviewing"

        # 4. Cycle status: interviewing -> hired -> rejected -> submitted
        c1 = await cycle_proposal_status(session, user_id, prop1.id)
        assert c1.status == "hired"

        c2 = await cycle_proposal_status(session, user_id, prop1.id)
        assert c2.status == "rejected"

        c3 = await cycle_proposal_status(session, user_id, prop1.id)
        assert c3.status == "submitted"

        # Non-existent proposal
        non_existent = await cycle_proposal_status(session, user_id, 99999)
        assert non_existent is None


# ============================================================================
# 3. TEST UPWORK CONTRACTS & EARNINGS
# ============================================================================

@pytest.mark.asyncio
async def test_contract_and_earnings_flow(setup_test_db):
    user_id = setup_test_db["user_id"]
    session_factory = setup_test_db["session_factory"]

    async with session_factory() as session:
        # 1. Add contract
        contract = await add_upwork_contract(
            session=session,
            user_id=user_id,
            client_name="Acme Corp",
            project_title="FastAPI + Telegram Integration",
            rate_or_budget_usd=500.0,
            contract_type="fixed",
            total_earned_usd=100.0,
        )
        assert contract.id is not None
        assert contract.status == "active"
        assert contract.total_earned_usd == 100.0

        # 2. Add earnings
        updated = await add_contract_earnings(session, user_id, contract.id, 250.0)
        assert updated is not None
        assert updated.total_earned_usd == 350.0

        # 3. Active contracts
        active_list = await get_active_contracts(session, user_id)
        assert len(active_list) == 1
        assert active_list[0].id == contract.id

        # 4. Complete contract
        completed = await complete_upwork_contract(
            session, user_id, contract.id, rating=5.0, feedback="Exceptional engineer!"
        )
        assert completed is not None
        assert completed.status == "completed"
        assert completed.rating == 5.0
        assert completed.feedback == "Exceptional engineer!"

        # Now active should be empty, all contracts should have 1
        active_list2 = await get_active_contracts(session, user_id)
        assert len(active_list2) == 0

        all_contracts = await get_all_contracts(session, user_id)
        assert len(all_contracts) == 1


# ============================================================================
# 4. TEST SUMMARY & FORMATTERS
# ============================================================================

@pytest.mark.asyncio
async def test_career_summary_and_formatters(setup_test_db):
    user_id = setup_test_db["user_id"]
    session_factory = setup_test_db["session_factory"]

    async with session_factory() as session:
        # Setup goal, 1 hired proposal, 1 contract with $400 earned
        await update_career_goal(session, user_id, target_revenue_usd=1000.0)
        p = await add_upwork_proposal(session, user_id, "Dev Job", bid_amount_usd=400.0, connects_spent=8)
        await update_proposal_status(session, user_id, p.id, "hired")

        c = await add_upwork_contract(session, user_id, "Client A", "Dev Job", 400.0, total_earned_usd=400.0)

        summary = await get_career_summary(session, user_id)
        assert summary["total_earned_usd"] == 400.0
        assert summary["target_revenue_usd"] == 1000.0
        assert summary["revenue_progress"] == 40
        assert summary["proposals_sent"] == 1
        assert summary["proposals_hired"] == 1
        assert summary["conversion_rate"] == 100.0
        assert summary["total_connects_spent"] == 8

        # Format dashboard
        dash_html = format_career_dashboard_html(summary, [c], [p])
        assert "UPWORK CAREER RADAR" in dash_html
        assert "$400 / $1,000" in dash_html
        assert "Client A" in dash_html

        # Format proposal list
        prop_html = format_proposals_list_html([p])
        assert "DAFTAR PROPOSAL UPWORK" in prop_html
        assert "Dev Job" in prop_html

        # Format empty proposal list
        empty_prop_html = format_proposals_list_html([])
        assert "Belum ada proposal" in empty_prop_html

        # Format contract list
        con_html = format_contracts_list_html([c])
        assert "DAFTAR KONTRAK KERJA UPWORK" in con_html
        assert "Client A" in con_html

        # Test progress bar
        bar0 = render_progress_bar(0)
        bar50 = render_progress_bar(50)
        bar100 = render_progress_bar(100)
        assert "[░░░░░░░░░░] 0%" in bar0
        assert "50%" in bar50
        assert "[██████████] 100%" in bar100


# ============================================================================
# 5. TEST BOT COMMANDS & CALLBACKS
# ============================================================================

@pytest.mark.asyncio
async def test_bot_career_commands_and_callbacks(setup_test_db):
    chat_id = setup_test_db["chat_id"]
    user_id = setup_test_db["user_id"]
    session_factory = setup_test_db["session_factory"]

    # 1. /karir command
    update = MockUpdate(chat_id=chat_id)
    ctx = MockContext()
    await bot_module.karir_cmd(update, ctx)
    assert len(update.effective_message.replies) == 1
    assert "UPWORK CAREER RADAR" in update.effective_message.replies[0]
    assert len(update.effective_message.reply_markups) == 1

    # 2. /proposal command with arguments
    update2 = MockUpdate(chat_id=chat_id)
    ctx2 = MockContext(args=["Frontend Next.js Lead", "|", "600", "|", "10"])
    await bot_module.proposal_cmd(update2, ctx2)
    assert len(update2.effective_message.replies) == 1
    assert "Proposal Upwork Berhasil Dicatat" in update2.effective_message.replies[0]
    assert "$600" in update2.effective_message.replies[0]

    # 3. /proposal command without arguments (list proposals)
    update3 = MockUpdate(chat_id=chat_id)
    ctx3 = MockContext(args=[])
    await bot_module.proposal_cmd(update3, ctx3)
    assert len(update3.effective_message.replies) == 1
    assert "DAFTAR PROPOSAL UPWORK" in update3.effective_message.replies[0]

    # 4. /kontrak command
    update4 = MockUpdate(chat_id=chat_id)
    ctx4 = MockContext()
    await bot_module.contracts_cmd(update4, ctx4)
    assert len(update4.effective_message.replies) == 1
    assert "KONTRAK KERJA UPWORK" in update4.effective_message.replies[0]

    # 5. Career callback: menu proposals & menu dashboard
    update_cb1 = MockUpdate(chat_id=chat_id, callback_data="career:menu:proposals")
    await bot_module.career_callback(update_cb1, ctx)
    assert update_cb1.callback_query.answered is True
    assert "DAFTAR PROPOSAL UPWORK" in update_cb1.callback_query.edited_text

    update_cb2 = MockUpdate(chat_id=chat_id, callback_data="career:menu:dashboard")
    await bot_module.career_callback(update_cb2, ctx)
    assert "UPWORK CAREER RADAR" in update_cb2.callback_query.edited_text

    # 6. Cycle proposal status callback
    async with session_factory() as session:
        props = await get_recent_proposals(session, user_id, limit=1)
        prop_id = props[0].id

    update_cb3 = MockUpdate(chat_id=chat_id, callback_data=f"career:cycle_prop:{prop_id}")
    await bot_module.career_callback(update_cb3, ctx)
    assert update_cb3.callback_query.answered is True

    # 7. Add earnings callback
    async with session_factory() as session:
        contract = await add_upwork_contract(session, user_id, "Test Client", "App Work", 500.0)
        contract_id = contract.id

    update_cb4 = MockUpdate(chat_id=chat_id, callback_data=f"career:earn:{contract_id}:50")
    await bot_module.career_callback(update_cb4, ctx)
    assert update_cb4.callback_query.answered is True
    assert "+$50" in update_cb4.callback_query.answer_text

    # 8. Unlinked user test
    unlinked_update = MockUpdate(chat_id=1111111)
    await bot_module.karir_cmd(unlinked_update, ctx)
    assert "belum terhubung" in unlinked_update.effective_message.replies[0]
