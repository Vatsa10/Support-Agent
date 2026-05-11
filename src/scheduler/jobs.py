import os
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db.pool import sys_conn
from observability.logging import get_logger
from tools.idempotency import finalize as idem_finalize

log = get_logger("scheduler")

_scheduler: AsyncIOScheduler | None = None


APPROVAL_TIMEOUT_HOURS = int(os.getenv("APPROVAL_TIMEOUT_HOURS", "24"))


async def _sweep_stale_approvals() -> None:
    """Auto-reject approvals older than APPROVAL_TIMEOUT_HOURS."""
    try:
        async with sys_conn() as conn:
            rows = await conn.fetch(
                """
                SELECT a.id, a.tenant_id, a.action_run_id, r.idempotency_key
                FROM approvals a
                JOIN action_runs r ON r.id = a.action_run_id
                WHERE a.status = 'pending'
                  AND a.created_at < now() - ($1 || ' hours')::interval
                """,
                str(APPROVAL_TIMEOUT_HOURS),
            )
            for r in rows:
                await conn.execute(
                    "UPDATE approvals SET status='timed_out', decision='reject', reason='approval_timeout', decided_at=now() WHERE id=$1",
                    r["id"],
                )
                await conn.execute(
                    "UPDATE action_runs SET status='denied', error='approval_timeout' WHERE id=$1",
                    r["action_run_id"],
                )
                if r["idempotency_key"]:
                    try:
                        await idem_finalize(
                            str(r["tenant_id"]), r["idempotency_key"], "failed",
                            {"timed_out": True},
                        )
                    except Exception as e:
                        log.warning("idem_finalize_failed", extra={"err": str(e)})
        if rows:
            log.info("approvals_timed_out", extra={"count": len(rows)})
    except Exception as e:
        log.error("sweep_stale_approvals_failed", extra={"err": str(e)})


def start_scheduler() -> None:
    global _scheduler
    if os.getenv("SCHEDULER_ENABLED", "true").lower() not in ("1", "true", "yes"):
        log.info("scheduler_disabled")
        return
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _sweep_stale_approvals,
        trigger=IntervalTrigger(minutes=15),
        id="approval_sweep",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )
    _scheduler.start()
    log.info("scheduler_started")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info("scheduler_stopped")
