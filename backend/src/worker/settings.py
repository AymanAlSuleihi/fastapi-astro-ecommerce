from pydantic_settings import BaseSettings, SettingsConfigDict
from taskiq import TaskiqScheduler
from taskiq_valkey import ListValkeyScheduleSource, ValkeyStreamBroker


class WorkerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VALKEY_")
    VALKEY_HOST: str = "valkey"
    VALKEY_PORT: int = 6379
    VALKEY_DB: int = 0


worker_config = WorkerConfig()

valkey_url = (
    f"valkey://{worker_config.VALKEY_HOST}:{worker_config.VALKEY_PORT}/{worker_config.VALKEY_DB}"
)

broker = ValkeyStreamBroker(valkey_url)

# Register tasks
import src.worker.tasks  # noqa: F401, E402

schedule_source = ListValkeyScheduleSource(
    valkey_url,
    schedules=[
        {
            "task_name": "fetch_exchange_rates",
            "labels": {},
            "cron": "0 6 * * *",  # daily at 6 AM
        },
    ],
)
scheduler = TaskiqScheduler(broker, [schedule_source])
