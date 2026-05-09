"""Celery tasks for the mortgage review flow."""
import logging
from celery import shared_task

from apps.agents.mortgage_engine import MortgageReviewEngine
from .models import MortgageApplication

logger = logging.getLogger(__name__)


@shared_task
def run_mortgage_review_task(application_id: str):
    """Run the 5-agent mortgage review for a given application."""
    try:
        application = MortgageApplication.objects.get(application_id=application_id)
    except MortgageApplication.DoesNotExist:
        logger.error("MortgageApplication %s not found", application_id)
        return

    try:
        MortgageReviewEngine().run(application)
    except Exception:
        logger.exception("Mortgage review aborted for application %s", application_id)
