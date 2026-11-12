from sqlalchemy import String, Integer, Float, Column, create_engine, Date, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime

USERNAME = "Aiman"
PASSWORD = "12345678"

db_path = "warehouse.db"
engine = create_engine(f"sqlite:///{db_path}")
# PostgreSQL instead (needs psycopg2-binary):
# engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5432/warehouse")
Base = declarative_base()

Statuses = ["pending", "dispatched"]
Batch_statuses = ["planned", "dispatched"]


class DispatchBatch(Base):
    __tablename__ = "DispatchBatches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    destination = Column(String)
    vehicle = Column(String)
    status = Column(String, default="planned")
    created_on = Column(DateTime, default=datetime.now)


class Package(Base):
    __tablename__ = "Packages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    destination = Column(String)
    weight = Column(Float)
    arrival_date = Column(Date)
    status = Column(String, default="pending")
    batch_id = Column(Integer, ForeignKey("DispatchBatches.id"), nullable=True)


Base.metadata.create_all(engine)


# E1: Register a package
def register_package(name, destination, weight, arrival_date, status="pending"):
    if not name.strip() or not destination.strip():
        return {"error": "name and destination cannot be empty"}
    if weight <= 0:
        return {"error": "weight must be greater than 0"}
    if status not in Statuses:
        return {"error": "status must be 'pending' or 'dispatched'"}
    try:
        arrival = datetime.strptime(arrival_date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "arrival_date must be in YYYY-MM-DD format"}

    with Session(engine) as session:
        package = Package(
            name=name.strip(),
            destination=destination.strip(),
            weight=weight,
            arrival_date=arrival,
            status=status,
        )
        session.add(package)
        session.commit()
        return {
            "id": package.id,
            "name": package.name,
            "destination": package.destination,
            "weight": package.weight,
            "arrival_date": str(package.arrival_date),
            "status": package.status,
        }

def verify_login(username, password):
    if username == USERNAME and password == PASSWORD:
        return True
    return False

