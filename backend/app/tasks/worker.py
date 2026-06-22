from arq import cron
from app.config import get_settings
from app.tasks.fetch_sources import fetch_all_sources
from app.tasks.send_newsletter import process_due_schedules
from app.tasks.generate_content import generate_content_task


async def startup(ctx: dict):
    import redis.asyncio as aioredis
    settings = get_settings()
    ctx["redis"] = await aioredis.from_url(settings.redis_url)


async def shutdown(ctx: dict):
    await ctx["redis"].aclose()


class WorkerSettings:
    functions = [generate_content_task, fetch_all_sources, process_due_schedules]
    on_startup = startup
    on_shutdown = shutdown
    cron_jobs = [
        cron(fetch_all_sources, minute={0, 30}),
        cron(process_due_schedules, second=0),
    ]
    redis_settings_from_env = True

    @staticmethod
    def redis_settings():
        from arq.connections import RedisSettings
        settings = get_settings()
        return RedisSettings.from_dsn(settings.redis_url)
