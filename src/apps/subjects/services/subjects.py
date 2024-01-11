import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from apps.subjects.crud import SubjectsCrud, SubjectsRespondentsCrud
from apps.subjects.db.schemas import SubjectRespondentSchema, SubjectSchema
from apps.subjects.domain import Subject, SubjectCreate, SubjectRespondent
from apps.users.services.user import UserService


class SubjectsService:
    def __init__(self, session: AsyncSession, user_id: uuid.UUID):
        self.session = session
        self.user_id = user_id

    async def _create_subject(self, schema: Subject) -> Subject:
        subj_crud = SubjectsCrud(self.session)
        subject = SubjectSchema(
            applet_id=schema.applet_id,
            email=schema.email,
            user_id=schema.user_id,
            creator_id=self.user_id,
            language=schema.language,
            nickname=schema.email,
            first_name=schema.first_name,
            last_name=schema.last_name,
            secret_user_id=schema.secret_user_id,
        )
        subject_entity = await subj_crud.save(subject)
        return Subject.from_orm(subject_entity)

    async def _create_subject_respondent(
        self, subject_id: uuid.UUID, schema: SubjectCreate
    ) -> SubjectRespondent:
        subj_resp_crud = SubjectsRespondentsCrud(self.session)
        subject_resp = SubjectRespondentSchema(
            subject_id=subject_id,
            relation=schema.relation,
            respondent_access_id=schema.respondent_access_id,
        )
        subj_resp_entity = await subj_resp_crud.save(subject_resp)
        return SubjectRespondent.from_orm(subj_resp_entity)

    async def create(self, schema: Subject) -> Subject:
        subject = await self._create_subject(schema)
        merged_data = subject.dict()
        return Subject(**merged_data)

    async def merge(self, subject_id: uuid.UUID) -> Subject | None:
        """
        Merge shell account with full account for current user
        """
        user = await UserService(self.session).get(self.user_id)
        assert user
        crud = SubjectsCrud(self.session)
        subject = await crud.get_by_id(subject_id)
        if subject:
            subject.user_id = user.id
            subject.email = user.email_encrypted
            subject.last_name = user.first_name
            subject.first_name = user.first_name
            await crud.update_by_id(subject)
            return Subject.from_orm(subject)
        return None

    async def is_secret_id_exist(
        self, secret_id: str, applet_id: uuid.UUID
    ) -> bool:
        return await SubjectsCrud(self.session).is_secret_id_exist(
            secret_id, applet_id
        )

    async def get_by_email(self, email: str) -> Subject | None:
        return await SubjectsCrud(self.session).get_by_email(email)

    async def get(self, id_: uuid.UUID) -> Subject | None:
        return await SubjectsCrud(self.session).get_by_id(id_)
