from datetime import datetime
from typing import ClassVar, override
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, Row
from sqlalchemy.orm import aliased

from app.core.schemas import UserBrief
from app.database.models import (
    ApmtStatus,
    Appointment,
    FortunePackage,
    User,
    Seer,
)
from ..seer.package.fortune.schemas import FPRequiredData


class UserBriefExtra(UserBrief):
    required: dict = Field(
        default_factory=dict,
        examples=[{
            "name": "Apinyawat Khwanpruk",
            "birthdate": "2002-10-03T00:00:00",
            "phone_number": "0812345678"
        }]
    )


class SeerBrief(UserBrief):
    name: str
    socials_name: str | None
    socials_link: str | None


class PackageBrief(BaseModel):
    seer_id: int
    id: int
    name: str
    category: str | None

    model_config = ConfigDict(from_attributes=True)


class AppointmentBrief(BaseModel):
    id: int
    client: UserBrief
    seer: UserBrief
    package: PackageBrief | None
    start_time: datetime
    end_time: datetime
    status: ApmtStatus
    confirmation_code: str

    model_config = ConfigDict(from_attributes=True)

    _client: ClassVar = aliased(User, name='client')
    _seer_u: ClassVar = aliased(User, name='seer_user')

    @classmethod
    def create_from(cls, obj: Row):
        if obj.package_id:
            package_brief = PackageBrief(
                seer_id=obj.seer_id, id=obj.package_id,
                name=obj.package_name, category=obj.package_category
            )
        else:
            package_brief = None
        return cls(
            id=obj.id,
            client=UserBrief(
                id=obj.client_id, display_name=obj.client_display_name,
                image=obj.client_image
            ),
            seer=UserBrief(
                id=obj.seer_id, display_name=obj.seer_display_name,
                image=obj.seer_image
            ),
            package=package_brief,
            start_time=obj.start_time,
            end_time=obj.end_time,
            status=obj.status,
            confirmation_code=obj.confirmation_code
        )

    @staticmethod
    def select(*extras):
        client = AppointmentBrief._client
        seer_u = AppointmentBrief._seer_u
        return (
            select(
                Appointment.id,
                client.id.label('client_id'),
                client.display_name.label('client_display_name'),
                client.image.label('client_image'),
                Seer.id.label('seer_id'),
                seer_u.display_name.label('seer_display_name'),
                seer_u.image.label('seer_image'),
                FortunePackage.id.label('package_id'),
                FortunePackage.name.label('package_name'),
                FortunePackage.category.label('package_category'),
                Appointment.start_time,
                Appointment.end_time,
                Appointment.status,
                Appointment.confirmation_code,
                *extras
            ).
            join(client, Appointment.client_id == client.id).
            join(seer_u, Appointment.seer_id == seer_u.id).
            join(Seer, seer_u.id == Seer.id).
            join(Appointment.package, isouter=True)
        )


class AppointmentOut(AppointmentBrief):
    client: UserBriefExtra
    seer: SeerBrief
    questions: list[str]
    date_created: datetime

    @override
    @classmethod
    def create_from(cls, obj: Row):
        req_dict = {
            "name": obj.client_name,
            "birthdate": obj.client_birthdate,
            "phone_number": obj.client_phone_number
        }
        required_info = {
            r.name: req_dict[r.name]
            for r in FPRequiredData
            if obj.required_data and obj.required_data & int(r.value)
        }
        if obj.package_id:
            package_brief = PackageBrief(
                seer_id=obj.seer_id, id=obj.package_id,
                name=obj.package_name, category=obj.package_category
            )
        else:
            package_brief = None
        return cls(
            id=obj.id,
            client=UserBriefExtra(
                id=obj.client_id, display_name=obj.client_display_name,
                image=obj.client_image,
                required=required_info
            ),
            seer=SeerBrief(
                id=obj.seer_id,
                display_name=obj.seer_display_name,
                image=obj.seer_image,
                name=obj.seer_name,
                socials_name=obj.socials_name,
                socials_link=obj.socials_link
            ),
            package=package_brief,
            start_time=obj.start_time,
            end_time=obj.end_time,
            status=obj.status,
            confirmation_code=obj.confirmation_code,
            questions=obj.questions,
            date_created=obj.date_created
        )

    @override
    @staticmethod
    def select(*extras):
        parent = super(AppointmentOut, AppointmentOut)
        client = parent._client
        seer_u = parent._seer_u
        return parent.select(
            Appointment.questions,
            Appointment.date_created,
            FortunePackage.required_data,
            (client.first_name + ' ' + client.last_name).label('client_name'),
            client.birthdate.label('client_birthdate'),
            client.phone_number.label('client_phone_number'),
            (seer_u.first_name + ' ' + seer_u.last_name).label('seer_name'),
            Seer.socials_name,
            Seer.socials_link,
            *extras
        )


class AppointmentPublic(BaseModel):
    id: int
    seer_id: int
    package_id: int
    start_time: datetime
    end_time: datetime
    status: ApmtStatus

    model_config = ConfigDict(from_attributes=True)


class AppointmentIn(BaseModel):
    seer_id: int
    package_id: int
    start_time: datetime
    questions: list[str]


class AppointmentId(BaseModel):
    apmt_id: int | None


class AppointmentCreated(AppointmentId):
    start_time: datetime
    code: str
    seer_id: int
    seer_display_name: str
    seer_socials_name: str | None
    seer_socials_link: str | None
    package_id: int
    package_name: str
    user_display_name: str
    total: float
