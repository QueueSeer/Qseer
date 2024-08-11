from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from .models import Base

engine = create_engine("sqlite:///./database.db", echo=True)


def get_session():
    with Session(engine) as session, session.begin():
        yield session


def create_tables():
    Base.metadata.create_all(engine)


# with Session(engine) as session:
#     spongebob = User(
#         name="spongebob",
#         fullname="Spongebob Squarepants",
#         addresses=[Address(email_address="spongebob@sqlalchemy.org")],
#     )
#     sandy = User(
#         name="sandy",
#         fullname="Sandy Cheeks",
#         addresses=[
#             Address(email_address="sandy@sqlalchemy.org"),
#             Address(email_address="sandy@squirrelpower.org"),
#         ],
#     )
#     patrick = User(name="patrick", fullname="Patrick Star")
#     session.add_all([spongebob, sandy, patrick])
#     session.commit()
