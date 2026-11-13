from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Session, declarative_base

ph = PasswordHasher()

STATUSES = ["pending", "dispatched"]
BATCH_STATUSES = ["planned", "dispatched"]
ROLES = ["admin", "staff", "viewer"]

# RBAC - which roles can use which routes
VIEW = ["admin", "staff", "viewer"]
EDIT = ["admin", "staff"]
ADMIN = ["admin"]

# First admin account, created automatically only if the users table is empty
ADMIN_USERNAME = "Aiman"
ADMIN_PASSWORD = "12345678"

ACCESS_TOKEN_EXPIRY = 15  # mins
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60  # mins
SECRET_KEY = "mysecret"
ALGORITHM = "HS256"

DATABASE_URL = "sqlite:///./packages.db"

engine = create_engine(DATABASE_URL)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="viewer", nullable=False)


class DispatchBatch(Base):
    __tablename__ = "dispatch_batches"

    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String, nullable=False)
    vehicle = Column(String, nullable=False)
    status = Column(String, default="planned", nullable=False)
    created_on = Column(DateTime, default=datetime.now)


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    arrival_date = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)
    batch_id = Column(Integer, ForeignKey("dispatch_batches.id"), nullable=True)


Base.metadata.create_all(engine)


# ---------- Password hashing ----------

def hash_password(password):
    return ph.hash(password)


def check_password(password, password_hash):
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


# ---------- Users ----------

def create_user(username, password, role):
    with Session(engine) as session:
        if session.query(User).filter(User.username == username).first():
            return None
        user = User(username=username, password_hash=hash_password(password), role=role)
        session.add(user)
        session.commit()
        return {"username": user.username, "role": user.role}


def get_user(username):
    with Session(engine) as session:
        user = session.query(User).filter(User.username == username).first()
        if user is None:
            return None
        return {"username": user.username, "role": user.role}


def seed_admin():
    with Session(engine) as session:
        has_users = session.query(User).first() is not None
    if not has_users:
        create_user(ADMIN_USERNAME, ADMIN_PASSWORD, "admin")


seed_admin()


# ---------- JWT ----------

def verify_login(username, password):
    with Session(engine) as session:
        user = session.query(User).filter(User.username == username).first()
        if user is None or not check_password(password, user.password_hash):
            return None
        name, role = user.username, user.role

    access_token = create_token(name, role, token_type="access")
    refresh_token = create_token(name, role, token_type="refresh")
    return {"access_token": access_token, "refresh_token": refresh_token}


def create_token(username, role, token_type):
    time = ACCESS_TOKEN_EXPIRY
    if token_type == "refresh":
        time = REFRESH_TOKEN_EXPIRY
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=time),
        "token_type": token_type,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token, token_type):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None

    if payload.get("token_type") != token_type:
        return None

    return payload


# ---------- RBAC ----------

def authorize(token, roles):
    payload = verify_token(token, "access")

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload["role"] not in roles:
        raise HTTPException(status_code=403, detail="You do not have permission for this action")

    return payload


def check_choice(value, allowed, field):
    if value is not None and value not in allowed:
        raise HTTPException(status_code=422, detail=f"{field} must be one of {allowed}")


# ---------- Packages ----------

def add_package(name, destination, weight, arrival_date, status):
    session = Session(engine)

    package = Package(
        name=name,
        destination=destination,
        weight=weight,
        arrival_date=arrival_date,
        status=status
    )

    session.add(package)
    session.commit()
    session.refresh(package)
    session.close()

    return package


def get_package(package_id):
    session = Session(engine)

    package = session.query(Package).filter(Package.id == package_id).first()

    session.close()

    return package


def update_package(
    package_id,
    name=None,
    destination=None,
    weight=None,
    arrival_date=None,
    status=None
):
    session = Session(engine)

    package = session.query(Package).filter(Package.id == package_id).first()

    if package is None:
        session.close()
        return None

    if name is not None:
        package.name = name

    if destination is not None:
        package.destination = destination

    if weight is not None:
        package.weight = weight

    if arrival_date is not None:
        package.arrival_date = arrival_date

    if status is not None:
        package.status = status

    session.commit()
    session.refresh(package)
    session.close()

    return package


def delete_package(package_id):
    session = Session(engine)

    package = session.query(Package).filter(Package.id == package_id).first()

    if package is None:
        session.close()
        return "not_found"

    if package.status == "dispatched":
        session.close()
        return "dispatched"

    session.delete(package)
    session.commit()
    session.close()

    return "deleted"


def get_packages(
    destination=None,
    status=None,
    arrival_date=None
):
    session = Session(engine)

    query = session.query(Package)

    if destination is not None:
        query = query.filter(Package.destination == destination)

    if status is not None:
        query = query.filter(Package.status == status)

    if arrival_date is not None:
        query = query.filter(Package.arrival_date == arrival_date)

    packages = query.all()
    session.close()
    return packages


# ---------- Dispatch batches ----------

def batch_to_dict(session, batch):
    packages = session.query(Package).filter(Package.batch_id == batch.id).all()
    return {
        "id": batch.id,
        "destination": batch.destination,
        "vehicle": batch.vehicle,
        "status": batch.status,
        "created_on": batch.created_on,
        "packages": [
            {
                "id": p.id,
                "name": p.name,
                "destination": p.destination,
                "weight": p.weight,
                "arrival_date": p.arrival_date,
                "status": p.status,
                "batch_id": p.batch_id,
            }
            for p in packages
        ],
    }


def create_batch(destination, vehicle, status, package_ids):
    ids = list(dict.fromkeys(package_ids))

    with Session(engine) as session:
        packages = session.query(Package).filter(Package.id.in_(ids)).all()
        found = {p.id: p for p in packages}

        for pid in ids:
            if pid not in found:
                return {"error": f"Package {pid} not found", "code": 404}

        for pid in ids:
            p = found[pid]
            if p.status == "dispatched" or p.batch_id is not None:
                return {"error": f"Package {pid} is already dispatched or in a batch", "code": 409}
            if p.destination.lower() != destination.lower():
                return {"error": f"Package {pid} destination does not match the batch", "code": 409}

        batch = DispatchBatch(destination=destination, vehicle=vehicle, status=status)
        session.add(batch)
        session.flush()  # gives batch.id

        for p in found.values():
            p.batch_id = batch.id
            if status == "dispatched":
                p.status = "dispatched"

        session.commit()
        return batch_to_dict(session, batch)


def get_batches(destination=None, vehicle=None, status=None):
    with Session(engine) as session:
        query = session.query(DispatchBatch)

        if destination is not None:
            query = query.filter(DispatchBatch.destination == destination)

        if vehicle is not None:
            query = query.filter(DispatchBatch.vehicle == vehicle)

        if status is not None:
            query = query.filter(DispatchBatch.status == status)

        return [batch_to_dict(session, b) for b in query.all()]


# ---------- Stats ----------

def get_summary():
    with Session(engine) as session:
        total = session.query(Package).count()
        dispatched = session.query(Package).filter(Package.status == "dispatched").count()
        rows = (
            session.query(Package.destination, func.count(Package.id))
            .group_by(Package.destination)
            .all()
        )
        return {
            "total_received": total,
            "total_pending": total - dispatched,
            "total_dispatched": dispatched,
            "destination_wise": {dest: count for dest, count in rows},
        }