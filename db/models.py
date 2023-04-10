""" database and models implementation """
from datetime import datetime as dt

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    DateTime,
    String,
    Boolean,
    ForeignKey,
    Float,
    JSON,
)
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


from dotenv import dotenv_values

BONOS_SQLALCHEMY_DATABASE_URI = dotenv_values(".env")["BONOS_SQLALCHEMY_DATABASE_URI"]

engine = create_engine(BONOS_SQLALCHEMY_DATABASE_URI)

SessionFactory = scoped_session(sessionmaker(bind=engine))

# session = sessionmaker(bind=engine)
# session = session()
# session = scoped_session(session_factory)

query = SessionFactory.query_property()

Base = declarative_base()

# https://stackoverflow.com/questions/15936111/sqlalchemy-can-you-add-custom-methods-to-the-query-object
Base.query = query

session = SessionFactory()


class Operation(Base):
    """operations rates for predefined types (following challenge requirements)"""

    __tablename__ = "operation"
    id = Column(Integer, primary_key=True)
    operation_type = Column(String, unique=True)
    alias = Column(String, unique=True)
    records = relationship("Record", backref="operation")
    cost = Column(Float)
    deleted_at = Column(Boolean, default=None, nullable=True)

    def __repr__(self):
        """dunder repr"""
        return self.operation_type

    def to_json(self):
        """json representation"""
        return {
            "id": self.id,
            "type": self.operation_type,
            "alias": self.alias,
            "cost": self.cost,
        }


class Record(Base):
    """user service consuption"""

    __tablename__ = "record"
    id = Column(Integer, primary_key=True)
    operation_id = Column(
        Integer, ForeignKey("operation.id")
    )  # user credit / debit needed
    users_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    user_balance = Column(Float)
    operation_response = Column(JSON)
    date = Column(DateTime, default=dt.utcnow)
    deleted_at = Column(Boolean, default=None, nullable=True)

    def __repr__(self):
        """dunder repr"""
        return self.operation_type

    def to_json(self):
        """json representation"""
        return {
            "id": self.id,
            "operation_type": self.operation.operation_type,
            "alias": self.operation.alias,
            "operation_response": self.operation_response,
            "date": self.date,
            "user_balance": self.user_balance,
            "amount": self.amount,
        }


class Users(UserMixin, Base):
    """user data"""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(100))  # user reges to valide email
    password = Column(String(100))
    status = Column(Boolean)
    records = relationship("Record", backref="users")
    deleted_at = Column(Boolean, default=None, nullable=True)

    def to_json(self):
        """json representation"""
        return {"id": self.id, "email": self.email, "status": self.status}

    def get_records(self):
        """access to user info"""
        return {"records": [r.to_json() for r in self.records]}

    def set_password(self, password):
        """sets password for the user on database"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """checks if password is correct"""
        return check_password_hash(self.password_hash, password)


def get_user_balance(email, start_balance):
    """credit information is on record table. if not default credit is given"""
    user = Users.query.filter_by(email=email).first()

    if user:
        balance = (
            Record.query.filter_by(users_id=user.id)
            .with_entities(Record.user_balance)
            .order_by(Record.id.desc())
            .first()
        )
        if balance:
            return balance.user_balance
        return float(start_balance)
    return 0
