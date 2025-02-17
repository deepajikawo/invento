from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
import enum

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

# Create database engine with proper configuration
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={'sslmode': 'require'}
)

# Create declarative base
Base = declarative_base()

class TransactionType(enum.Enum):
    ADD = "add"
    UPDATE = "update"
    REMOVE = "remove"

class PaymentMethod(enum.Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    MOBILE_PAYMENT = "mobile_payment"

class Phone(Base):
    __tablename__ = 'phones'

    id = Column(Integer, primary_key=True)
    model = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Sale(Base):
    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True)
    phone_model = Column(String, nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    customer_name = Column(String)
    customer_phone = Column(String)
    sale_date = Column(DateTime, default=datetime.now)
    notes = Column(String)

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    phone_model = Column(String, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    previous_quantity = Column(Integer, nullable=False)
    new_quantity = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    notes = Column(String)

# Create all tables
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)