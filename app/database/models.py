import datetime as dt
import re
from enum import Enum as pyEnum
from decimal import Decimal
from typing import Annotated, Any

from sqlalchemy import (
    BigInteger,
    CHAR,
    CheckConstraint,
    Column,
    DDL,
    FetchedValue,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Numeric,
    Table,
    Text,
    TIMESTAMP,
    Time,
    event,
    func,
    and_,
    text,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    foreign,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, REAL, SMALLINT
from sqlalchemy.engine import Connection
from sqlalchemy.sql import compiler

# Overwrite FK_ON_DELETE to allow set null one of the composite key
compiler.FK_ON_DELETE = re.compile(
    r"^(?:RESTRICT|CASCADE|SET NULL|SET NULL\s?(.*)|NO ACTION|SET DEFAULT)$", re.I
)

intPK = Annotated[int, mapped_column(primary_key=True)]
strText = Annotated[str, mapped_column(Text())]
timestamp = Annotated[
    dt.datetime,
    mapped_column(
        TIMESTAMP(timezone=True)
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
    int | None,
    mapped_column(
        ForeignKey("userAccount.id", ondelete='SET NULL')
    )
]
seerFK = Annotated[
    int | None,
    mapped_column(
        ForeignKey("seer.id", ondelete='SET NULL')
    )
]
intPK_userFK = Annotated[
    int,
    mapped_column(
        ForeignKey("userAccount.id", ondelete="CASCADE"),
        primary_key=True
    )
]
intPK_seerFK = Annotated[
    int,
    mapped_column(
        ForeignKey("seer.id", ondelete="CASCADE"),
        primary_key=True
    )
]


class Base(AsyncAttrs, DeclarativeBase):
    pass


FollowSeer = Table(
    "followSeer",
    Base.metadata,
    Column(
        "user_id", ForeignKey("userAccount.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "seer_id", ForeignKey("seer.id", ondelete="CASCADE"),
        primary_key=True
    )
)
'''Contains `user_id` and `seer_id` columns'''


'''
 █████  █████                           
  ███    ███                            
  ███    ███   █████   ██████  ████████ 
  ███    ███  ███     ███  ███  ███  ███
  ███    ███   █████  ███████   ███     
  ███    ███      ███ ███       ███     
   ████████   ██████   ██████  █████    
'''
class User(Base):
    __tablename__ = "userAccount"

    id: Mapped[intPK] = mapped_column(Identity())
    username: Mapped[strText | None] = mapped_column(unique=True)
    display_name: Mapped[strText]
    first_name: Mapped[strText]
    last_name: Mapped[strText]
    email: Mapped[strText] = mapped_column(unique=True)
    password: Mapped[strText | None] = mapped_column(
        server_default=text("null"), deferred=True
    )
    birthdate: Mapped[timestamp | None] = mapped_column(
        server_default=text("null")
    )
    phone_number: Mapped[str | None] = mapped_column(CHAR(10), nullable=True)
    coins: Mapped[coin] = mapped_column(server_default=text("0"))
    image: Mapped[strText] = mapped_column(server_default=text("''"))
    is_active: Mapped[bool] = mapped_column(
        server_default=text("false"), deferred=True
    )
    date_created: Mapped[timestamp] = mapped_column(
        server_default=func.now(), deferred=True
    )
    properties: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'"), deferred=True
    )

    # back_populates: name of the relationship attribute in the other model
    seer: Mapped["Seer | None"] = relationship(
        primaryjoin=lambda: and_(User.id == Seer.id, Seer.is_active == True),
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )  # on delete cascade
    # admin: Mapped["Admin | None"] = relationship(
    #     passive_deletes="all"
    # )
    # following: Mapped[list["Seer"]] = relationship(
    #     secondary=FollowSeer,
    #     back_populates="followers",
    #     cascade="all, delete",
    #     passive_deletes=True
    # )  # on delete cascade
    # appointments: Mapped[list["Appointment"]] = relationship(
    #     back_populates="client",
    #     passive_deletes=True
    # )  # on delete set null
    # question_answers: Mapped[list["QuestionAnswer"]] = relationship(
    #     back_populates="client",
    #     passive_deletes=True
    # )  # on delete set null
    # bids: Mapped[list["BidInfo"]] = relationship(
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )  # on delete cascade
    # sent_transactions: Mapped[list["Transaction"]] = relationship(
    #     back_populates="sender",
    #     foreign_keys="Transaction.sender_id",
    #     passive_deletes=True
    # )  # on delete set null
    # received_transactions: Mapped[list["Transaction"]] = relationship(
    #     back_populates="receiver",
    #     foreign_keys="Transaction.receiver_id",
    #     passive_deletes=True
    # )  # on delete set null
    # reports: Mapped[list["Report"]] = relationship(
    #     back_populates="reporter",
    #     passive_deletes=True
    # )  # on delete set null
    # notification: Mapped[list["NotificationHistory"]] = relationship(
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )  # on delete cascade

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[intPK_userFK]
    date_created: Mapped[timestamp] = mapped_column(
        server_default=func.now(), deferred=True
    )


'''
  █████████                             
 ███     ███                            
 ███          ██████   ██████  ████████ 
  █████████  ███  ███ ███  ███  ███  ███
         ███ ███████  ███████   ███     
 ███     ███ ███      ███       ███     
  █████████   ██████   ██████  █████    
'''
class Seer(Base):
    __tablename__ = "seer"

    id: Mapped[intPK_userFK]
    experience: Mapped[dt.date | None] = mapped_column(
        server_default=text("null")
    )
    description: Mapped[strText] = mapped_column(server_default=text("''"))
    primary_skill: Mapped[strText | None] = mapped_column(
        server_default=text("null")
    )
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())
    is_available: Mapped[bool] = mapped_column(server_default=text("true"))
    is_active: Mapped[bool] = mapped_column(server_default=text("false"))
    verified_at: Mapped[timestamp | None] = mapped_column(
        server_default=text("null")
    )
    socials_name: Mapped[strText | None] = mapped_column(
        server_default=text("null")
    )
    socials_link: Mapped[strText | None] = mapped_column(
        server_default=text("null")
    )
    rating: Mapped[float | None] = mapped_column(
        REAL(), server_default=text("null")
    )
    review_count: Mapped[int] = mapped_column(server_default=text("0"))
    break_duration: Mapped[dt.timedelta] = mapped_column(
        server_default=text("'0'")
    )
    bank_name: Mapped[strText | None] = mapped_column(
        server_default=text("null") # PromptPay
    )
    bank_no: Mapped[strText | None] = mapped_column(
        server_default=text("null")
    )
    properties: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'"), deferred=True
    )

    user: Mapped[User] = relationship(
        back_populates="seer",
        single_parent=True
    )
    # followers: Mapped[list[User]] = relationship(
    #     secondary=FollowSeer,
    #     back_populates="following",
    #     cascade="all, delete",
    #     passive_deletes=True
    # )
    # schedule: Mapped[list["Schedule"]] = relationship(
    #     back_populates="seer",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )
    # day_offs: Mapped[list["DayOff"]] = relationship(
    #     back_populates="seer",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )
    # withdrawals: Mapped[list["Withdrawal"]] = relationship(
    #     back_populates="seer",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )
    # fortune_packages: Mapped[list["FortunePackage"]] = relationship(
    #     back_populates="seer",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )
    # question_packages: Mapped[list["QuestionPackage"]] = relationship(
    #     back_populates="seer",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )
    # appointments: Mapped[list["Appointment"]] = relationship(
    #     back_populates="seer",
    #     passive_deletes=True
    # )
    # question_answers: Mapped[list["QuestionAnswer"]] = relationship(
    #     back_populates="seer",
    #     passive_deletes=True
    # )
    # auctions: Mapped[list["AuctionInfo"]] = relationship(
    #     back_populates="seer",
    #     passive_deletes="all"
    # )  # on delete restrict


class Schedule(Base):
    __tablename__ = "seerSchedule"

    seer_id: Mapped[intPK_seerFK]
    id: Mapped[intPK] = mapped_column(FetchedValue())
    start_time: Mapped[dt.time] = mapped_column(Time(timezone=True))
    end_time: Mapped[dt.time] = mapped_column(Time(timezone=True))
    # 0: Monday, 1: Tuesday, ..., 6: Sunday
    day: Mapped[int] = mapped_column(SMALLINT)

    # seer: Mapped[Seer] = relationship(back_populates="schedule")


class DayOff(Base):
    __tablename__ = "dayOff"

    seer_id: Mapped[intPK_seerFK]
    day_off: Mapped[dt.date] = mapped_column(primary_key=True)

    # seer: Mapped[Seer] = relationship(back_populates="day_offs")


class WdStatus(str, pyEnum):
    pending = "pending"
    completed = "completed"
    rejected = "rejected"


class Withdrawal(Base):
    __tablename__ = "withdrawal"

    id: Mapped[intPK] = mapped_column(Identity())
    requester_id: Mapped[int] = mapped_column(
        ForeignKey(Seer.id, ondelete="CASCADE")
    )
    amount: Mapped[coin]
    bank_name: Mapped[strText | None] = mapped_column(
        server_default=text("null")
    )
    bank_no: Mapped[strText | None] = mapped_column(
        server_default=text("null")
    )
    status: Mapped[WdStatus] = mapped_column(server_default=text("'pending'"))
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())
    txn_id: Mapped[int] = mapped_column(
        ForeignKey("transaction.id"), unique=True
    )

    # seer: Mapped[Seer] = relationship(back_populates="withdrawals")


'''
 ███████████                     █████                                 
  ███     ███                     ███                                  
  ███     ███  ██████    ██████   ███ █████  ██████    ███████  ██████ 
  ██████████       ███  ███  ███  ███  ███       ███  ███  ███ ███  ███
  ███          ███████  ███       ██████     ███████  ███  ███ ███████ 
  ███         ███  ███  ███  ███  ███  ███  ███  ███  ███  ███ ███     
 █████         ████████  ██████  ████ █████  ████████  ███████  ██████ 
                                                           ███         
                                                      ███  ███         
                                                       ██████          
'''
class FPStatus(str, pyEnum):
    draft = "draft"
    published = "published"
    hidden = "hidden"


class FPChannel(str, pyEnum):
    chat = "chat"
    phone = "phone"
    video = "video"


class FortunePackage(Base):
    __tablename__ = "fortunePackage"

    seer_id: Mapped[intPK_seerFK]
    id: Mapped[intPK] = mapped_column(FetchedValue())
    name: Mapped[strText]
    price: Mapped[coin | None] = mapped_column(server_default=text("null"))
    duration: Mapped[dt.timedelta | None] = mapped_column(
        server_default=text("null")
    )
    description: Mapped[strText] = mapped_column(server_default=text("''"))
    question_limit: Mapped[int] = mapped_column(
        SMALLINT, server_default=text("0")
    )
    status: Mapped[FPStatus] = mapped_column(server_default=text("'draft'"))
    foretell_channel: Mapped[FPChannel] = mapped_column(
        server_default=text("'chat'")
    )
    reading_type: Mapped[strText | None] = mapped_column(
        server_default=text("null")
    )
    category: Mapped[strText | None] = mapped_column(
        server_default=text("null")
    )
    # None, None, ..., Telephone, Birthdate, Name
    required_data: Mapped[int] = mapped_column(
        SMALLINT, server_default=text("0")
    )
    image: Mapped[strText] = mapped_column(server_default=text("''"))
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())

    # seer: Mapped[Seer] = relationship(back_populates="fortune_packages")


class QuestionPackage(Base):
    __tablename__ = "questionPackage"

    seer_id: Mapped[intPK_seerFK]
    id: Mapped[intPK] = mapped_column(FetchedValue())
    price: Mapped[coin]
    description: Mapped[strText] = mapped_column(server_default=text("''"))
    enable_at: Mapped[timestamp | None] = mapped_column(
        server_default=func.now()
    )
    stack_limit: Mapped[int | None] = mapped_column(server_default=text("100"))
    image: Mapped[strText] = mapped_column(server_default=text("''"))
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())

    # seer: Mapped[Seer] = relationship(back_populates="question_packages")


class Activity(Base):
    __tablename__ = "activity"

    id: Mapped[intPK] = mapped_column(BigInteger, Identity())
    type: Mapped[strText]
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())

    __mapper_args__ = {
        "polymorphic_identity": "activity",
        "polymorphic_on": "type",
    }


class ApmtStatus(str, pyEnum):
    pending = "pending"
    u_cancelled = "u_cancelled"
    s_cancelled = "s_cancelled"
    completed = "completed"
    other = "other"


class Appointment(Activity):
    __tablename__ = "appointment"

    id: Mapped[intPK] = mapped_column(
        ForeignKey(Activity.id, ondelete="CASCADE")
    )
    client_id: Mapped[userFK]
    seer_id: Mapped[seerFK]
    f_package_id: Mapped[int | None]
    start_time: Mapped[timestamp] = mapped_column(server_default=func.now())
    end_time: Mapped[timestamp] = mapped_column(server_default=func.now())
    status: Mapped[ApmtStatus]
    questions: Mapped[list[str]] = mapped_column(
        ARRAY(Text()), server_default=text("'{}'")
    )
    confirmation_code: Mapped[strText] = mapped_column(
        server_default=text("''")
    )

    # client: Mapped[User | None] = relationship(
    #     back_populates="appointments"
    # )
    # seer: Mapped[Seer | None] = relationship(
    #     back_populates="appointments"
    # )
    package: Mapped[FortunePackage | None] = relationship(
        primaryjoin=lambda: and_(
            foreign(Appointment.f_package_id) == FortunePackage.id,
            Appointment.seer_id == FortunePackage.seer_id
        ),
    )

    __mapper_args__ = {
        "polymorphic_identity": "appointment"
    }

    __table_args__ = (
        ForeignKeyConstraint(
            ["seer_id", "f_package_id"],
            [FortunePackage.seer_id, FortunePackage.id],
            ondelete="SET NULL (f_package_id)",
        ),
        CheckConstraint(
            "client_id IS NOT NULL and seer_id IS NOT NULL",
            name="client_seer_not_null"
        )
    )


class QuestionAnswer(Activity):
    __tablename__ = "questionAnswer"

    id: Mapped[intPK] = mapped_column(
        ForeignKey(Activity.id, ondelete="CASCADE")
    )
    client_id: Mapped[userFK]
    seer_id: Mapped[seerFK]
    q_package_id: Mapped[int | None]
    question: Mapped[strText]
    question_at: Mapped[timestamp] = mapped_column(server_default=func.now())
    answer: Mapped[strText | None]
    answer_at: Mapped[timestamp | None] = mapped_column(
        server_default=text("null")
    )

    # client: Mapped[User | None] = relationship(
    #     back_populates="question_answers"
    # )
    # seer: Mapped[Seer | None] = relationship(
    #     back_populates="question_answers"
    # )
    package: Mapped[QuestionPackage | None] = relationship(
        primaryjoin=lambda: and_(
            foreign(QuestionAnswer.q_package_id) == QuestionPackage.id, 
            QuestionAnswer.seer_id == QuestionPackage.seer_id
        )
    )

    __mapper_args__ = {
        "polymorphic_identity": "questionAnswer"
    }

    __table_args__ = (
        ForeignKeyConstraint(
            ["seer_id", "q_package_id"],
            [QuestionPackage.seer_id, QuestionPackage.id],
            ondelete="SET NULL (q_package_id)",
        ),
        CheckConstraint(
            "client_id IS NOT NULL and seer_id IS NOT NULL",
            name="client_seer_not_null"
        )
    )


class AuctionInfo(Activity):
    __tablename__ = "auctionInfo"

    id: Mapped[intPK] = mapped_column(
        ForeignKey(Activity.id, ondelete="CASCADE")
    )
    seer_id: Mapped[int] = mapped_column(
        ForeignKey(Seer.id, ondelete="RESTRICT")
    )
    name: Mapped[strText]
    short_description: Mapped[strText] = mapped_column(
        server_default=text("''")
    )
    description: Mapped[strText] = mapped_column(server_default=text("''"))
    image: Mapped[strText] = mapped_column(server_default=text("''"))
    start_time: Mapped[timestamp] = mapped_column(server_default=func.now())
    end_time: Mapped[timestamp] = mapped_column(server_default=func.now())
    appoint_start_time: Mapped[timestamp] = mapped_column(
        server_default=func.now()
    )
    appoint_end_time: Mapped[timestamp] = mapped_column(
        server_default=func.now()
    )
    initial_bid: Mapped[coin] = mapped_column(server_default=text("20"))
    min_increment: Mapped[coin] = mapped_column(server_default=text("10"))

    # seer: Mapped[Seer] = relationship(back_populates="auctions")
    bid_info: Mapped[list["BidInfo"]] = relationship(
        back_populates="auction",
        passive_deletes="all"
    )  # on delete restrict

    __mapper_args__ = {
        "polymorphic_identity": "auctionInfo"
    }


class BidInfo(Base):
    __tablename__ = "bidInfo"

    auction_id: Mapped[intPK] = mapped_column(
        ForeignKey(AuctionInfo.id, ondelete="RESTRICT"),
    )
    user_id: Mapped[intPK_userFK]
    amount: Mapped[coin]

    auction: Mapped[AuctionInfo] = relationship(back_populates="bid_info")
    # user: Mapped[User] = relationship(back_populates="bids")


'''
 ███████████                       
 █   ███   █                       
     ███     █████ █████ ████████  
     ███      ███   ███   ███  ███ 
     ███        █████     ███  ███ 
     ███      ███   ███   ███  ███ 
    █████    █████ █████ ████ █████
'''
class TxnType(str, pyEnum):
    topup = "topup"
    withdraw = "withdraw"
    appointment = "appointment"
    question = "question"
    auction_bid = "auction_bid"
    auction_earn = "auction_earn"
    transfer = "transfer"
    other = "other"


class TxnStatus(str, pyEnum):
    completed = "completed"
    hold = "hold"
    cancelled = "cancelled"


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[intPK] = mapped_column(BigInteger, Identity())
    user_id: Mapped[userFK]
    activity_id: Mapped[int | None] = mapped_column(
        ForeignKey(Activity.id, ondelete="SET NULL")
    )
    amount: Mapped[coin]
    type: Mapped[TxnType]
    status: Mapped[TxnStatus]
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())

    # sender: Mapped[User | None] = relationship(
    #     back_populates="sent_transactions",
    #     foreign_keys="Transaction.sender_id"
    # )
    # receiver: Mapped[User | None] = relationship(
    #     back_populates="received_transactions",
    #     foreign_keys="Transaction.receiver_id"
    # )
    activity: Mapped[Activity | None] = relationship()

    __table_args__ = (
        Index(
            'ix_transaction_user_id_activity_id',
            'user_id', 'activity_id'
        ),
    )


class Review(Base):
    __tablename__ = "review"

    id: Mapped[intPK] = mapped_column(
        ForeignKey(Activity.id, ondelete="CASCADE")
    )
    score: Mapped[int] = mapped_column(
        SMALLINT, CheckConstraint("0 <= score AND score <= 5")
    )
    text: Mapped[strText] = mapped_column(server_default=text("''"))
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())

    report: Mapped[list["Report"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class Report(Base):
    __tablename__ = "report"

    id: Mapped[intPK] = mapped_column(Identity())
    user_id: Mapped[userFK]
    review_id: Mapped[int] = mapped_column(
        ForeignKey(Review.id, ondelete="CASCADE")
    )
    reason: Mapped[strText] = mapped_column(server_default=text("''"))
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())

    # reporter: Mapped[User] = relationship(back_populates="reports")
    review: Mapped[Review | None] = relationship(back_populates="report")


class NotificationHistory(Base):
    __tablename__ = "notificationHistory"

    user_id: Mapped[intPK_userFK]
    id: Mapped[intPK] = mapped_column(FetchedValue())
    activity_id: Mapped[int | None] = mapped_column(
        ForeignKey(Activity.id, ondelete="SET NULL")
    )
    transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey(Transaction.id, ondelete="SET NULL")
    )
    content: Mapped[strText]
    type: Mapped[strText]
    date_created: Mapped[timestamp] = mapped_column(server_default=func.now())

    # user: Mapped[User] = relationship(back_populates="notification")
    activity: Mapped[Activity | None] = relationship()
    transaction: Mapped[Transaction | None] = relationship()


counter_tables = DDL('''\
CREATE TABLE IF NOT EXISTS "scheduleCounter" (
    id INTEGER PRIMARY KEY,
    counter INTEGER DEFAULT 1 NOT NULL,
    FOREIGN KEY (id) REFERENCES "seer" (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "fPackageCounter" (
    id INTEGER PRIMARY KEY,
    counter INTEGER DEFAULT 1 NOT NULL,
    FOREIGN KEY (id) REFERENCES "seer" (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "qPackageCounter" (
    id INTEGER PRIMARY KEY,
    counter INTEGER DEFAULT 1 NOT NULL,
    FOREIGN KEY (id) REFERENCES "seer" (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "notificationCounter" (
    id INTEGER PRIMARY KEY,
    counter INTEGER DEFAULT 1 NOT NULL,
    FOREIGN KEY (id) REFERENCES "userAccount" (id) ON DELETE CASCADE
);
''').execute_if(dialect='postgresql')

funcs = DDL("""\
CREATE OR REPLACE FUNCTION increment_composite() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.id IS NOT NULL THEN
		EXECUTE format(
	        'UPDATE %%I SET counter=$1.id
			WHERE %%I.id = $1.%%I AND counter < $1.id',
			TG_ARGV[0], TG_ARGV[0], TG_ARGV[1]
	    )
		USING NEW;
	    RETURN NEW;
	END IF;

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
CREATE OR REPLACE TRIGGER pk_increment BEFORE INSERT ON "seerSchedule"
FOR EACH ROW EXECUTE PROCEDURE increment_composite('scheduleCounter', 'seer_id');

CREATE OR REPLACE TRIGGER pk_increment BEFORE INSERT ON "fortunePackage"
FOR EACH ROW EXECUTE PROCEDURE increment_composite('fPackageCounter', 'seer_id');

CREATE OR REPLACE TRIGGER pk_increment BEFORE INSERT ON "questionPackage"
FOR EACH ROW EXECUTE PROCEDURE increment_composite('qPackageCounter', 'seer_id');

CREATE OR REPLACE TRIGGER pk_increment BEFORE INSERT ON "notificationHistory"
FOR EACH ROW EXECUTE PROCEDURE increment_composite('notificationCounter', 'user_id');
""").execute_if(dialect='postgresql')


@event.listens_for(Base.metadata, 'after_create')
def receive_after_create(target, connection: Connection, **kw):
    if kw.get('tables', None):
        connection.execute(counter_tables)
        connection.execute(funcs)
        connection.execute(triggers)
