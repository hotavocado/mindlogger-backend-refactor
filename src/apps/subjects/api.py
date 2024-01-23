import uuid

from fastapi import Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.authentication.deps import get_current_user
from apps.shared.domain import Response
from apps.shared.exception import NotFoundError
from apps.subjects.domain import (
    Subject,
    SubjectCreateRequest,
    SubjectFull,
    SubjectRespondentCreate,
)
from apps.subjects.services import SubjectsService
from apps.users import User
from apps.workspaces.domain.constants import Role
from apps.workspaces.service.check_access import CheckAccessService
from apps.workspaces.service.user_applet_access import UserAppletAccessService
from infrastructure.database import atomic
from infrastructure.database.deps import get_session


async def create_subject(
    user: User = Depends(get_current_user),
    schema: SubjectCreateRequest = Body(...),
    session: AsyncSession = Depends(get_session),
) -> Response[Subject]:
    async with atomic(session):
        subject_sch = Subject(
            applet_id=schema.applet_id,
            creator_id=user.id,
            language=schema.language,
            first_name=schema.first_name,
            last_name=schema.last_name,
            nickname=schema.nickname,
            secret_user_id=schema.secret_user_id,
            email=schema.email,
        )
        subject = await SubjectsService(session, user.id).create(subject_sch)
        return Response(result=Subject.from_orm(subject))


async def add_respondent(
    user: User = Depends(get_current_user),
    schema: SubjectRespondentCreate = Body(...),
    session: AsyncSession = Depends(get_session),
) -> Response[SubjectFull]:
    await CheckAccessService(session, user.id).check_applet_invite_access(
        schema.applet_id
    )
    async with atomic(session):
        service = SubjectsService(session, user.id)
        await service.check_exist(schema.subject_id, schema.applet_id)
        subject_full = await service.add_respondent(
            respondent_id=schema.user_id,
            subject_id=schema.subject_id,
            applet_id=schema.applet_id,
            relation=schema.relation,
        )
        return Response(result=subject_full)


async def remove_respondent(
    subject_id: uuid.UUID,
    respondent_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Response[SubjectFull]:
    async with atomic(session):
        service = SubjectsService(session, user.id)
        subject = await service.get(subject_id)
        if not subject:
            raise NotFoundError()
        await CheckAccessService(session, user.id).check_applet_invite_access(
            subject.applet_id
        )
        access = await UserAppletAccessService(
            session, respondent_id, subject.applet_id
        ).get_access(Role.RESPONDENT)
        if not access:
            raise NotFoundError()
        subject = await service.remove_respondent(access.id, subject_id)
        return Response(result=subject)