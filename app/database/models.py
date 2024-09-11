import datetime as dt
import re
from decimal import Decimal
from typing import Annotated

from sqlalchemy import (
    BigInteger,
    CHAR,
    CheckConstraint,
    DDL,
    FetchedValue,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Numeric,
    Text,
    TIMESTAMP,
    Time,
    event,
    func,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    composite,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import SMALLINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.engine import Connection
from sqlalchemy.sql import compiler
from sqlalchemy.schema import CreateTable

from .composite import Name

# Overwrite FK_ON_DELETE to allow set null one of the composite key
compiler.FK_ON_DELETE = re.compile(
    r"^(?:RESTRICT|CASCADE|SET NULL|SET NULL\s?(.*)|NO ACTION|SET DEFAULT)$", re.I
)

intPK = Annotated[int, mapped_column(primary_key=True)]
strText = Annotated[str, mapped_column(Text())]
timestamp = Annotated[
    dt.datetime,
    mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )
]
coin = Annotated[
    Decimal,
    mapped_column(
        Numeric(precision=15, scale=2),
        server_default=text("0")
    )
]

userFK = Annotated[
    int,
    mapped_column(
        ForeignKey("userAccount.id", ondelete='SET NULL')
    )
]
intPK_userFK = Annotated[
    int,
    mapped_column(
        ForeignKey("userAccount.id", ondelete="CASCADE"),
        primary_key=True
    )
]


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "userAccount"

    id: Mapped[intPK] = mapped_column(Identity())
    name: Mapped[Name] = composite(
        mapped_column("first_name", Text()),
        mapped_column("middle_name", Text(), nullable=True),
        mapped_column("last_name", Text())
    )
    role: Mapped[strText]
    email: Mapped[strText]
    birthdate: Mapped[dt.date | None]
    phone_number: Mapped[str | None] = mapped_column(CHAR(10), nullable=True)
    coins: Mapped[coin]
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())
    password: Mapped[strText]

    # back_populates: name of the relationship attribute in the other model class
    config: Mapped["UserConfig"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes="all"
    )
    schedule: Mapped["Schedule | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes="all"
    )
    package: Mapped[list["Package"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    # Appointment that this user made
    appointing: Mapped[list["Appointment"]] = relationship(
        back_populates="client",
        passive_deletes=True
    )
    # Appointment that other user made
    appointed: Mapped[list["Appointment"]] = relationship(
        back_populates="seer",
        passive_deletes=True
    )
    bids: Mapped[list["BidInfo"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    post: Mapped[list["Post"]] = relationship(
        back_populates="user",
        passive_deletes=True
    )
    comment: Mapped[list["Comment"]] = relationship(
        back_populates="user",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r})"


class UserConfig(Base):
    __tablename__ = "userConfig"

    user_id: Mapped[intPK_userFK]
    email_notification: Mapped[bool] = mapped_column(
        server_default=text("false")
    )
    line_notification: Mapped[bool] = mapped_column(
        server_default=text("false")
    )

    user: Mapped[User] = relationship(
        back_populates="config",
        single_parent=True
    )


class Schedule(Base):
    __tablename__ = "userSchedule"

    user_id: Mapped[intPK_userFK]
    start_time: Mapped[dt.time] = mapped_column(
        Time(timezone=True), server_default=text("'00:00:00'")
    )
    end_time: Mapped[dt.time] = mapped_column(
        Time(timezone=True), server_default=text("'00:00:00'")
    )
    # Mon-Sun, 0 = Off, 1 = On
    # Example: 124 = 0b1111100 = Off Sat & Sun
    recurring_days_off: Mapped[int] = mapped_column(
        SMALLINT, server_default=text("0")
    )

    user: Mapped[User] = relationship(
        back_populates="schedule", single_parent=True
    )
    days_off: Mapped[list["DaysOff"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )


class DaysOff(Base):
    __tablename__ = "daysOff"

    schedule_id: Mapped[intPK] = mapped_column(
        ForeignKey(Schedule.user_id, ondelete="CASCADE")
    )
    day_off: Mapped[dt.date] = mapped_column(primary_key=True)


class Package(Base):
    __tablename__ = "package"

    user_id: Mapped[intPK_userFK]
    id: Mapped[intPK] = mapped_column(FetchedValue())
    name: Mapped[strText]
    price: Mapped[coin]
    duration: Mapped[dt.timedelta] = mapped_column(server_default=text("'0s'"))
    description: Mapped[strText] = mapped_column(server_default=text("''"))

    user: Mapped[User] = relationship(back_populates="package")
    appointment: Mapped[list["Appointment"]] = relationship(
        back_populates="package",
        passive_deletes="all"
    )


class Appointment(Base):
    __tablename__ = "appointment"

    id: Mapped[intPK] = mapped_column(BigInteger, Identity())
    client_id: Mapped[userFK | None]
    seer_id: Mapped[userFK | None]
    package_id: Mapped[int | None]
    start_time: Mapped[timestamp] = mapped_column(server_default=func.now())
    end_time: Mapped[timestamp] = mapped_column(server_default=func.now())
    status: Mapped[strText]

    client: Mapped[User] = relationship(
        back_populates="appointing",
        foreign_keys="client_id"
    )
    seer: Mapped[User] = relationship(
        back_populates="appointed",
        foreign_keys="seer_id"
    )
    package: Mapped[Package] = relationship(
        back_populates="appointment",
        foreign_keys="[seer_id, package_id]"
    )
    review: Mapped["Review | None"] = relationship(
        back_populates="appointment",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    auction_info: Mapped["AuctionInfo | None"] = relationship(
        back_populates="appointment",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["seer_id", "package_id"], [Package.user_id, Package.id],
            ondelete="SET NULL (package_id)",
        ),
    )


class Review(Base):
    __tablename__ = "review"

    appointment_id: Mapped[int] = mapped_column(
        ForeignKey(Appointment.id, ondelete="CASCADE"), primary_key=True
    )
    score: Mapped[int] = mapped_column(
        SMALLINT, CheckConstraint("0 <= score AND score <= 5")
    )
    text: Mapped[strText] = mapped_column(server_default=text("''"))
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())

    appointment: Mapped[Appointment] = relationship(
        back_populates="review", single_parent=True
    )


class AuctionInfo(Base):
    __tablename__ = "auctionInfo"

    appointment_id: Mapped[int] = mapped_column(
        ForeignKey(Appointment.id, ondelete="CASCADE"), primary_key=True
    )
    start_time: Mapped[timestamp] = mapped_column(server_default=func.now())
    end_time: Mapped[timestamp] = mapped_column(server_default=func.now())
    initial_bid: Mapped[coin]
    min_increment: Mapped[coin]

    appointment: Mapped[Appointment] = relationship(
        back_populates="auction_info", single_parent=True
    )
    bid_info: Mapped[list["BidInfo"]] = relationship(
        back_populates="auction",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class BidInfo(Base):
    __tablename__ = "bidInfo"

    auction_id: Mapped[intPK] = mapped_column(
        ForeignKey(AuctionInfo.appointment_id, ondelete="CASCADE")
    )
    user_id: Mapped[intPK_userFK]
    amount: Mapped[coin]

    auction: Mapped[AuctionInfo] = relationship(back_populates="bid_info")
    user: Mapped[User] = relationship(back_populates="bids")


class Post(Base):
    __tablename__ = "post"

    id: Mapped[intPK] = mapped_column(Identity())
    user_id: Mapped[userFK | None]
    markdown: Mapped[strText]
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())

    user: Mapped[User] = relationship(back_populates="post")


class Comment(Base):
    __tablename__ = "comment"

    post_id: Mapped[intPK] = mapped_column(
        ForeignKey(Post.id, ondelete="CASCADE")
    )
    id: Mapped[intPK] = mapped_column(FetchedValue())
    user_id: Mapped[userFK | None]
    text: Mapped[strText]
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())

    user: Mapped[User] = relationship(back_populates="comment")


counter_tables = DDL('''\
CREATE TABLE IF NOT EXISTS "packageCounter" (
    id INTEGER PRIMARY KEY,
    counter INTEGER DEFAULT 1 NOT NULL,
    FOREIGN KEY (id) REFERENCES "userAccount" (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "commentCounter" (
    id INTEGER PRIMARY KEY,
    counter INTEGER DEFAULT 1 NOT NULL,
    FOREIGN KEY (id) REFERENCES "post" (id) ON DELETE CASCADE
);
'''   ).execute_if(dialect='postgresql')

funcs = DDL("""\
CREATE OR REPLACE FUNCTION increment_composite() RETURNS TRIGGER AS $$
BEGIN
    EXECUTE format(
        'INSERT INTO %%I (id, counter) values ($1.%%I, 1)
        ON CONFLICT (id) DO UPDATE SET counter=%%I.counter+1
        returning counter', TG_ARGV[0], TG_ARGV[1], TG_ARGV[0]
    )
	INTO NEW.id
	USING NEW;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""").execute_if(dialect='postgresql')

triggers = DDL("""\
CREATE OR REPLACE TRIGGER package_increment BEFORE INSERT ON "package"
FOR EACH ROW EXECUTE PROCEDURE increment_composite('packageCounter', 'user_id');

CREATE OR REPLACE TRIGGER package_increment BEFORE INSERT ON "comment"
FOR EACH ROW EXECUTE PROCEDURE increment_composite('commentCounter', 'post_id');
""").execute_if(dialect='postgresql')


@event.listens_for(Base.metadata, 'after_create')
def receive_after_create(target, connection: Connection, **kw):
    if kw.get('tables', None):
        connection.execute(counter_tables)
        connection.execute(funcs)
        connection.execute(triggers)
