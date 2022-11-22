"""
This module includes all the models which should be tracked by alembic

They are imported here to make sure, that they are visible to alembic
when it imports the declarative 'Base' from this module.

Import all SQLAlchemy models here
"""

from infrastructure.database import Base  # noqa: F401, F403
