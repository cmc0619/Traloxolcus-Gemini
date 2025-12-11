from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started.")
            
    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped.")
            
    def add_job(self, func, trigger_type='cron', **trigger_args):
        try:
            if trigger_type == 'cron':
                trigger = CronTrigger(**trigger_args)
                self.scheduler.add_job(func, trigger)
                logger.info(f"Added cron job {func.__name__} with args {trigger_args}")
            else:
                # Fallback or other types if needed
                pass
        except Exception as e:
            logger.error(f"Failed to add job: {e}")

scheduler_service = SchedulerService()
