from datetime import datetime, timezone
from sqlalchemy import select
from croniter import croniter

from app.db.session import AsyncSessionLocal
from app.db.models.schedule import Schedule, ScheduleStatus
from app.db.models.generated_content import GeneratedContent


async def process_due_schedules(ctx: dict) -> dict:
    now = datetime.now(timezone.utc)
    sent = 0
    errors = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Schedule).where(
                Schedule.is_active == True,
                Schedule.status == ScheduleStatus.pending,
                Schedule.send_at <= now,
            )
        )
        schedules = result.scalars().all()

        for schedule in schedules:
            try:
                content_result = await db.execute(
                    select(GeneratedContent).where(
                        GeneratedContent.id == schedule.generated_content_id
                    )
                )
                content = content_result.scalar_one_or_none()
                if not content:
                    schedule.status = ScheduleStatus.failed
                    schedule.error_message = "Content not found"
                    continue

                from app.services.delivery import send_newsletter
                await send_newsletter(
                    subject=content.subject_line or content.title,
                    body_html=content.body_html,
                    recipient_list=schedule.recipient_list,
                )

                schedule.last_sent_at = now
                if schedule.cron_expression:
                    cron = croniter(schedule.cron_expression, now)
                    schedule.send_at = cron.get_next(datetime)
                    schedule.status = ScheduleStatus.pending
                else:
                    schedule.status = ScheduleStatus.sent

                sent += 1

            except Exception as e:
                schedule.status = ScheduleStatus.failed
                schedule.error_message = str(e)
                errors += 1

        await db.commit()

    return {"sent": sent, "errors": errors}
