"""ORM models.

Importing this package ensures that every model is registered on
``Base.metadata`` so that Alembic autogenerate (and ``alembic env.py``) can see
the full set of tables.
"""

from careeros_api.models.application import Application
from careeros_api.models.application_stage_history import ApplicationStageHistory
from careeros_api.models.company import Company
from careeros_api.models.contact import Contact
from careeros_api.models.document import Document
from careeros_api.models.interview import Interview
from careeros_api.models.note import Note
from careeros_api.models.pipeline_stage import PipelineStage
from careeros_api.models.reminder import Reminder
from careeros_api.models.subscription import Subscription
from careeros_api.models.user import User

__all__ = [
    "Application",
    "ApplicationStageHistory",
    "Company",
    "Contact",
    "Document",
    "Interview",
    "Note",
    "PipelineStage",
    "Reminder",
    "Subscription",
    "User",
]
