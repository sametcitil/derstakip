from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
import logging

from app.domain.risk import RiskEngine
from app.infrastructure import storage

# Configure logging
logger = logging.getLogger(__name__)


def nightly_job():
    """
    Nightly job to check student risk levels.
    Runs at 3:00 AM daily.
    """
    logger.info("Running nightly risk assessment job")
    
    try:
        engine = RiskEngine(storage)
        high_risk_students = []
        
        for student in storage.iter_all_students():
            risk = engine.calculate(student)
            
            if risk > 0.75:
                high_risk_students.append((student.id, student.name, risk))
                logger.warning(f"⚠️  High risk for student {student.id} ({student.name}): {risk:.2f}")
        
        # Log summary
        if high_risk_students:
            logger.info(f"Found {len(high_risk_students)} high-risk students")
        else:
            logger.info("No high-risk students found")
            
    except Exception as e:
        logger.error(f"Error in nightly risk assessment job: {e}", exc_info=True)


def start_scheduler(app: FastAPI) -> AsyncIOScheduler:
    """
    Start the scheduler for background tasks.
    
    Args:
        app: The FastAPI application instance
        
    Returns:
        The scheduler instance
    """
    scheduler = AsyncIOScheduler()
    
    # Add nightly job to run at 3:00 AM
    scheduler.add_job(
        nightly_job,
        CronTrigger(hour=3, minute=0),
        id="nightly_risk_assessment",
        replace_existing=True
    )
    
    # Store scheduler in app state
    app.state.scheduler = scheduler
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started with nightly risk assessment job")
    
    return scheduler 