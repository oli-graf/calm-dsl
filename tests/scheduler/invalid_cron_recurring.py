import uuid

from calm.dsl.builtins import Job
from calm.dsl.cli.scheduler import JobScheduler


class JobInvalidRecurringSpec(Job):
    """Recurring Job for Executing a Runbook with invalid cron"""

    name = "test_job_invalid_cron_recurring_" + str(uuid.uuid4())
    schedule_info = JobScheduler.ScheduleInfo.recurring(
        "15 1 32 * *", "2050-05-12T12:10:19Z", "2050-05-14T12:10:19Z"
    )
    executable = JobScheduler.Exec.runbook("invalid_cron_recurring", "")
