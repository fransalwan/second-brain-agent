# apps/backend/app/career.py
"""Modul Upwork Career Engine (Target Revenue, Proposal Pipeline, Connects ROI, & Contracts).

Menyediakan fungsi pendukung untuk:
- Pelacakan target pendapatan bulanan ($ USD & konversi IDR) dengan progress bar
- Pipeline pengajuan proposal (submitted -> interviewing -> hired -> completed)
- Pemantauan saldo/pengeluaran Connects dan conversion ROI
- Manajemen kontrak aktif klien, akumulasi pendapatan, dan rating kepuasan
"""

from datetime import datetime, timezone
import html
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, desc, func, select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .config import settings
from .models import CareerGoal, UpworkContract, UpworkProposal, utcnow

LOCAL_TZ = ZoneInfo(settings.APP_TIMEZONE)

PROPOSAL_STATUS_CYCLE = ["submitted", "interviewing", "hired", "rejected"]
STATUS_BADGES = {
    "draft": "📝 Draft",
    "submitted": "📨 Terkirim",
    "interviewing": "💬 Interview",
    "hired": "🎉 Hired / Kontrak",
    "rejected": "❌ Ditolak / Closed",
    "withdrawn": "↩️ Ditarik",
}


def render_progress_bar(percent: int, length: int = 10) -> str:
    """Menghasilkan visual progress bar bergaya [████░░░░░░]."""
    clamped = max(0, min(100, percent))
    filled_len = int(round(length * clamped / 100))
    bar = "█" * filled_len + "░" * (length - filled_len)
    return f"[{bar}] {clamped}%"


def get_current_month_str() -> str:
    """Mengembalikan bulan berjalan dalam format YYYY-MM berdasarkan APP_TIMEZONE."""
    now_local = datetime.now(LOCAL_TZ)
    return now_local.strftime("%Y-%m")


# ============================================================================
# 1. CAREER GOALS & TARGET REVENUE
# ============================================================================

async def get_or_create_monthly_career_goal(
    session: AsyncSession,
    user_id: UUID,
    month_str: Optional[str] = None,
) -> CareerGoal:
    """Mengambil atau membuat target karir bulanan pengguna."""
    target_month = month_str or get_current_month_str()
    stmt = select(CareerGoal).where(
        CareerGoal.user_id == user_id,
        CareerGoal.month == target_month,
    )
    res = await session.execute(stmt)
    goal = res.scalars().first()

    if not goal:
        goal = CareerGoal(
            user_id=user_id,
            month=target_month,
            target_revenue_usd=1000.0,
            target_proposals_count=20,
            current_badge="Rising Talent",
            usd_to_idr_rate=16200.0,
            created_at=utcnow(),
        )
        session.add(goal)
        await session.commit()
        await session.refresh(goal)

    return goal


async def update_career_goal(
    session: AsyncSession,
    user_id: UUID,
    month_str: Optional[str] = None,
    target_revenue_usd: Optional[float] = None,
    target_proposals_count: Optional[int] = None,
    current_badge: Optional[str] = None,
    usd_to_idr_rate: Optional[float] = None,
) -> CareerGoal:
    """Memperbarui parameter target karir bulanan pengguna."""
    goal = await get_or_create_monthly_career_goal(session, user_id, month_str)

    if target_revenue_usd is not None:
        goal.target_revenue_usd = max(0.0, target_revenue_usd)
    if target_proposals_count is not None:
        goal.target_proposals_count = max(0, target_proposals_count)
    if current_badge is not None:
        goal.current_badge = current_badge.strip()
    if usd_to_idr_rate is not None:
        goal.usd_to_idr_rate = max(1.0, usd_to_idr_rate)

    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return goal


# ============================================================================
# 2. UPWORK PROPOSALS PIPELINE
# ============================================================================

async def add_upwork_proposal(
    session: AsyncSession,
    user_id: UUID,
    job_title: str,
    bid_amount_usd: Optional[float] = None,
    connects_spent: int = 8,
    client_country: Optional[str] = None,
    job_url: Optional[str] = None,
    notes: Optional[str] = None,
) -> UpworkProposal:
    """Mencatat proposal baru yang diajukan di Upwork."""
    proposal = UpworkProposal(
        user_id=user_id,
        job_title=job_title.strip(),
        bid_amount_usd=bid_amount_usd,
        connects_spent=max(0, connects_spent),
        client_country=client_country.strip() if client_country else None,
        job_url=job_url.strip() if job_url else None,
        status="submitted",
        notes=notes.strip() if notes else None,
        submitted_at=utcnow(),
        created_at=utcnow(),
    )
    session.add(proposal)
    await session.commit()
    await session.refresh(proposal)
    return proposal


async def get_recent_proposals(
    session: AsyncSession,
    user_id: UUID,
    limit: int = 10,
    status_filter: Optional[str] = None,
) -> List[UpworkProposal]:
    """Mengambil daftar proposal terbaru pengguna."""
    query = select(UpworkProposal).where(UpworkProposal.user_id == user_id)
    if status_filter:
        query = query.where(UpworkProposal.status == status_filter)
    query = query.order_by(desc(UpworkProposal.submitted_at)).limit(limit)

    res = await session.execute(query)
    return list(res.scalars().all())


async def update_proposal_status(
    session: AsyncSession,
    user_id: UUID,
    proposal_id: int,
    new_status: str,
) -> Optional[UpworkProposal]:
    """Mengubah status proposal (submitted, interviewing, hired, rejected, dll)."""
    stmt = select(UpworkProposal).where(
        UpworkProposal.id == proposal_id,
        UpworkProposal.user_id == user_id,
    )
    res = await session.execute(stmt)
    proposal = res.scalars().first()
    if not proposal:
        return None

    proposal.status = new_status.strip().lower()
    session.add(proposal)
    await session.commit()
    await session.refresh(proposal)
    return proposal


async def cycle_proposal_status(
    session: AsyncSession,
    user_id: UUID,
    proposal_id: int,
) -> Optional[UpworkProposal]:
    """Memutar status proposal secara sirkular: submitted -> interviewing -> hired -> rejected -> submitted."""
    stmt = select(UpworkProposal).where(
        UpworkProposal.id == proposal_id,
        UpworkProposal.user_id == user_id,
    )
    res = await session.execute(stmt)
    proposal = res.scalars().first()
    if not proposal:
        return None

    curr = proposal.status.lower()
    if curr in PROPOSAL_STATUS_CYCLE:
        idx = PROPOSAL_STATUS_CYCLE.index(curr)
        next_status = PROPOSAL_STATUS_CYCLE[(idx + 1) % len(PROPOSAL_STATUS_CYCLE)]
    else:
        next_status = "submitted"

    proposal.status = next_status
    session.add(proposal)
    await session.commit()
    await session.refresh(proposal)
    return proposal


# ============================================================================
# 3. UPWORK CONTRACTS & CLIENT EARNINGS
# ============================================================================

async def add_upwork_contract(
    session: AsyncSession,
    user_id: UUID,
    client_name: str,
    project_title: str,
    rate_or_budget_usd: float,
    contract_type: str = "fixed",
    proposal_id: Optional[int] = None,
    total_earned_usd: float = 0.0,
    deadline: Optional[datetime] = None,
) -> UpworkContract:
    """Mencatat kontrak proyek Upwork baru."""
    contract = UpworkContract(
        user_id=user_id,
        proposal_id=proposal_id,
        client_name=client_name.strip(),
        project_title=project_title.strip(),
        contract_type=contract_type.strip().lower(),
        rate_or_budget_usd=max(0.0, rate_or_budget_usd),
        total_earned_usd=max(0.0, total_earned_usd),
        status="active",
        deadline=deadline,
        created_at=utcnow(),
    )
    session.add(contract)
    await session.commit()
    await session.refresh(contract)
    return contract


async def get_active_contracts(
    session: AsyncSession,
    user_id: UUID,
) -> List[UpworkContract]:
    """Mengambil daftar kontrak yang sedang berjalan aktif."""
    stmt = (
        select(UpworkContract)
        .where(
            UpworkContract.user_id == user_id,
            UpworkContract.status == "active",
        )
        .order_by(desc(UpworkContract.created_at))
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def get_all_contracts(
    session: AsyncSession,
    user_id: UUID,
    limit: int = 10,
) -> List[UpworkContract]:
    """Mengambil daftar seluruh kontrak (aktif & selesai)."""
    stmt = (
        select(UpworkContract)
        .where(UpworkContract.user_id == user_id)
        .order_by(desc(UpworkContract.created_at))
        .limit(limit)
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def add_contract_earnings(
    session: AsyncSession,
    user_id: UUID,
    contract_id: int,
    amount_usd: float,
) -> Optional[UpworkContract]:
    """Menambahkan pencairan dana/earning yang diterima dari kontrak tertentu."""
    stmt = select(UpworkContract).where(
        UpworkContract.id == contract_id,
        UpworkContract.user_id == user_id,
    )
    res = await session.execute(stmt)
    contract = res.scalars().first()
    if not contract:
        return None

    contract.total_earned_usd = max(0.0, contract.total_earned_usd + amount_usd)
    session.add(contract)
    await session.commit()
    await session.refresh(contract)
    return contract


async def complete_upwork_contract(
    session: AsyncSession,
    user_id: UUID,
    contract_id: int,
    rating: float = 5.0,
    feedback: Optional[str] = None,
) -> Optional[UpworkContract]:
    """Menandai kontrak selesai dengan rating dan feedback klien."""
    stmt = select(UpworkContract).where(
        UpworkContract.id == contract_id,
        UpworkContract.user_id == user_id,
    )
    res = await session.execute(stmt)
    contract = res.scalars().first()
    if not contract:
        return None

    contract.status = "completed"
    contract.rating = min(5.0, max(1.0, rating))
    if feedback:
        contract.feedback = feedback.strip()
    session.add(contract)
    await session.commit()
    await session.refresh(contract)
    return contract


# ============================================================================
# 4. SUMMARY & KPI CALCULATION
# ============================================================================

async def get_career_summary(
    session: AsyncSession,
    user_id: UUID,
    month_str: Optional[str] = None,
) -> dict:
    """Menghitung ringkasan KPI performa karir Upwork bulan ini."""
    goal = await get_or_create_monthly_career_goal(session, user_id, month_str)

    # 1. Hitung total earning dari kontrak pengguna
    contracts_res = await session.execute(
        select(UpworkContract).where(UpworkContract.user_id == user_id)
    )
    all_contracts = contracts_res.scalars().all()
    total_earned_usd = sum(c.total_earned_usd for c in all_contracts)
    active_contracts_count = sum(1 for c in all_contracts if c.status == "active")
    completed_contracts_count = sum(1 for c in all_contracts if c.status == "completed")

    # 2. Hitung statistik proposal bulan ini
    proposals_res = await session.execute(
        select(UpworkProposal).where(UpworkProposal.user_id == user_id)
    )
    all_proposals = proposals_res.scalars().all()
    proposals_sent = len(all_proposals)
    proposals_interviewing = sum(1 for p in all_proposals if p.status == "interviewing")
    proposals_hired = sum(1 for p in all_proposals if p.status == "hired")
    proposals_rejected = sum(1 for p in all_proposals if p.status == "rejected")
    total_connects_spent = sum(p.connects_spent for p in all_proposals)

    # 3. Hitung persentase dan konversi
    target_usd = goal.target_revenue_usd if goal.target_revenue_usd > 0 else 1000.0
    revenue_progress = int((total_earned_usd / target_usd) * 100)
    earned_idr = int(total_earned_usd * goal.usd_to_idr_rate)
    target_idr = int(target_usd * goal.usd_to_idr_rate)

    conversion_rate = (
        round((proposals_hired / proposals_sent) * 100, 1) if proposals_sent > 0 else 0.0
    )

    return {
        "month": goal.month,
        "target_revenue_usd": target_usd,
        "total_earned_usd": total_earned_usd,
        "earned_idr": earned_idr,
        "target_idr": target_idr,
        "revenue_progress": revenue_progress,
        "usd_to_idr_rate": goal.usd_to_idr_rate,
        "badge": goal.current_badge,
        "target_proposals": goal.target_proposals_count,
        "proposals_sent": proposals_sent,
        "proposals_interviewing": proposals_interviewing,
        "proposals_hired": proposals_hired,
        "proposals_rejected": proposals_rejected,
        "total_connects_spent": total_connects_spent,
        "active_contracts_count": active_contracts_count,
        "completed_contracts_count": completed_contracts_count,
        "conversion_rate": conversion_rate,
    }


# ============================================================================
# 5. HTML FORMATTERS FOR TELEGRAM
# ============================================================================

def format_career_dashboard_html(
    summary: dict,
    active_contracts: List[UpworkContract],
    recent_proposals: List[UpworkProposal],
) -> str:
    """Memformat dashboard utama karir Upwork ke HTML ramah Telegram."""
    month_name = summary["month"]
    badge = summary["badge"]
    earned_usd = summary["total_earned_usd"]
    target_usd = summary["target_revenue_usd"]
    earned_idr_str = f"Rp {summary['earned_idr']:,}".replace(",", ".")
    target_idr_str = f"Rp {summary['target_idr']:,}".replace(",", ".")
    rev_progress = summary["revenue_progress"]
    rev_bar = render_progress_bar(rev_progress, length=8)

    sent = summary["proposals_sent"]
    target_prop = summary["target_proposals"]
    prop_bar = render_progress_bar(
        int((sent / target_prop * 100) if target_prop > 0 else 0), length=8
    )

    lines = [
        "💼 <b>UPWORK CAREER RADAR &amp; DASHBOARD</b>",
        f"📅 Bulan: <b>{html.escape(month_name)}</b> | Status: <b>{html.escape(badge)}</b>",
        "",
        "🎯 <b>Target Pendapatan (Revenue Goal):</b>",
        f"{rev_bar} <b>${earned_usd:,.0f} / ${target_usd:,.0f} ({rev_progress}%)</b>",
        f"💵 <i>Estimasi IDR: {earned_idr_str} / {target_idr_str}</i>",
        "",
        "📊 <b>Pipeline Proposal &amp; Funnel:</b>",
        f"{prop_bar} <b>{sent} / {target_prop} Proposal Terkirim</b>",
        f"• 💬 Sedang Interview: <b>{summary['proposals_interviewing']}</b>",
        f"• 🎉 Hired / Menang: <b>{summary['proposals_hired']}</b>",
        f"• 📈 Conversion Rate: <b>{summary['conversion_rate']}%</b>",
        f"• 🪙 Connects Terpakai: <b>{summary['total_connects_spent']} connects</b>",
        "",
        "📂 <b>Kontrak Berjalan Aktif:</b>",
    ]

    if not active_contracts:
        lines.append("<i>Belum ada kontrak aktif saat ini. Kirim proposal untuk peluang baru!</i>")
    else:
        for c in active_contracts[:3]:
            rate_info = f"${c.rate_or_budget_usd:,.0f} ({c.contract_type})"
            earned_info = f"Earned: ${c.total_earned_usd:,.0f}"
            deadline_str = ""
            if c.deadline:
                now = datetime.now(timezone.utc)
                dl = c.deadline if c.deadline.tzinfo else c.deadline.replace(tzinfo=timezone.utc)
                days_left = (dl.date() - now.date()).days
                deadline_str = f" | ⏳ H-{days_left}" if days_left >= 0 else " | ⚠️ Lewat Deadline"

            lines.append(
                f"• <b>{html.escape(c.project_title)}</b>\n"
                f"  🏢 {html.escape(c.client_name)} | {rate_info} | {earned_info}{deadline_str}"
            )

    lines.append("")
    lines.append("📨 <b>Proposal Terkini:</b>")
    if not recent_proposals:
        lines.append("<i>Belum ada catatan proposal. Kirim /proposal untuk mencatat.</i>")
    else:
        for p in recent_proposals[:3]:
            st_badge = STATUS_BADGES.get(p.status, p.status)
            bid_str = f" (${p.bid_amount_usd:,.0f})" if p.bid_amount_usd else ""
            lines.append(f"• <b>{html.escape(p.job_title)}</b>{bid_str} [{st_badge}]")

    return "\n".join(lines)


def format_proposals_list_html(proposals: List[UpworkProposal]) -> str:
    """Memformat daftar seluruh proposal ke HTML Telegram."""
    if not proposals:
        return "📋 <b>DAFTAR PROPOSAL UPWORK</b>\n\n<i>Belum ada proposal yang dicatat.</i>"

    lines = [
        "📋 <b>DAFTAR PROPOSAL UPWORK</b>",
        f"Total tercatat: <b>{len(proposals)} proposal</b>\n",
    ]

    for p in proposals:
        st_badge = STATUS_BADGES.get(p.status, p.status)
        bid = f"${p.bid_amount_usd:,.0f}" if p.bid_amount_usd else "-"
        country = f" ({p.client_country})" if p.client_country else ""
        date_str = p.submitted_at.strftime("%d/%m") if p.submitted_at else ""

        lines.append(
            f"• <b>{html.escape(p.job_title)}</b>\n"
            f"  Status: <b>{st_badge}</b> | Bid: <b>{bid}</b> | 🪙 {p.connects_spent} connects{country} | 📅 {date_str}"
        )

    lines.append("\n💡 <i>Gunakan tombol di bawah untuk mengubah status proposal.</i>")
    return "\n".join(lines)


def format_contracts_list_html(contracts: List[UpworkContract]) -> str:
    """Memformat daftar seluruh kontrak kerja Upwork ke HTML Telegram."""
    if not contracts:
        return "💼 <b>KONTRAK KERJA UPWORK</b>\n\n<i>Belum ada kontrak tercatat.</i>"

    lines = [
        "💼 <b>DAFTAR KONTRAK KERJA UPWORK</b>",
        f"Total: <b>{len(contracts)} kontrak</b>\n",
    ]

    for c in contracts:
        st_icon = "🟢 Aktif" if c.status == "active" else "🏁 Selesai"
        rate_str = f"${c.rate_or_budget_usd:,.0f}"
        earned_str = f"${c.total_earned_usd:,.0f}"
        rating_str = f" | ⭐ {c.rating:.1f}" if c.rating else ""

        lines.append(
            f"• <b>{html.escape(c.project_title)}</b> [{st_icon}]\n"
            f"  🏢 Klien: <b>{html.escape(c.client_name)}</b> | Budget: <b>{rate_str}</b> | Cair: <b>{earned_str}</b>{rating_str}"
        )
        if c.feedback:
            lines.append(f"  💬 <i>\"{html.escape(c.feedback)}\"</i>")

    return "\n".join(lines)


# ============================================================================
# 6. INLINE KEYBOARD BUILDERS
# ============================================================================

def build_career_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Keyboard navigasi utama untuk Dashboard Karir Upwork."""
    keyboard = [
        [
            InlineKeyboardButton("📋 Kelola Proposal", callback_data="career:menu:proposals"),
            InlineKeyboardButton("💼 Daftar Kontrak", callback_data="career:menu:contracts"),
        ],
        [
            InlineKeyboardButton("➕ Tambah Earning ($)", callback_data="career:menu:earnings"),
            InlineKeyboardButton("🔄 Refresh Radar", callback_data="career:menu:refresh"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_proposals_list_keyboard(proposals: List[UpworkProposal]) -> InlineKeyboardMarkup:
    """Keyboard untuk memutar status proposal 1-tap."""
    keyboard = []
    for p in proposals[:5]:
        st_label = STATUS_BADGES.get(p.status, p.status)
        btn_text = f"🔄 {p.job_title[:18]}.. ({st_label})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"career:cycle_prop:{p.id}")])

    keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Dashboard", callback_data="career:menu:dashboard")])
    return InlineKeyboardMarkup(keyboard)


def build_contracts_list_keyboard(contracts: List[UpworkContract]) -> InlineKeyboardMarkup:
    """Keyboard untuk daftar kontrak."""
    keyboard = []
    for c in contracts[:4]:
        if c.status == "active":
            btn_text = f"💵 +$50 Earning ({c.client_name[:12]})"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"career:earn:{c.id}:50")])

    keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Dashboard", callback_data="career:menu:dashboard")])
    return InlineKeyboardMarkup(keyboard)
