import uuid

from apps.activities.domain.activity_create import (
    ActivityCreate,
    ActivityItemCreate,
)
from apps.applets.domain.applet_create import AppletCreate


class LdAppletCreate(AppletCreate):
    password: str | None = None
    extra_fields: dict


class LdActivityCreate(ActivityCreate):
    key: uuid.UUID | None = None
    extra_fields: dict


class LdActivityItemCreate(ActivityItemCreate):  # TODO
    extra_fields: dict