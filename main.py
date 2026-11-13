from datetime import date

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import function

app = FastAPI(title="Warehouse Dispatch Management System")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# PYDANTIC MODELS - validate the data coming in
class Login(BaseModel):
    username: str
    password: str


class RegisterUser(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    role: str = "viewer"


class Package(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=100)
    weight: float = Field(gt=0)
    arrival_date: date
    status: str = "pending"


class UpdatePackage(BaseModel):
    name: str = Field(default=None, min_length=1, max_length=100)
    destination: str = Field(default=None, min_length=1, max_length=100)
    weight: float = Field(default=None, gt=0)
    arrival_date: date = None
    status: str = None


class DispatchBatch(BaseModel):
    destination: str = Field(min_length=1, max_length=100)
    vehicle: str = Field(min_length=1, max_length=50)
    status: str = "planned"
    package_ids: list[int] = Field(min_length=1)


# LOGIN
@app.post("/login")
def login(data: Login):
    tokens = function.verify_login(username=data.username, password=data.password)

    if tokens is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return tokens


# REFRESH TOKEN
@app.post("/refresh")
def refresh(refresh_token: str = Header(None)):
    payload = function.verify_token(refresh_token, "refresh")

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = function.get_user(payload["username"])

    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")

    access_token = function.create_token(user["username"], user["role"], token_type="access")
    return {"access_token": access_token}


# REGISTER USER (admin only)
@app.post("/users", status_code=201)
def register_user(data: RegisterUser, token: str = Header(None)):
    function.authorize(token, function.ADMIN)
    function.check_choice(data.role, function.ROLES, "role")

    user = function.create_user(data.username, data.password, data.role)

    if user is None:
        raise HTTPException(status_code=409, detail="Username already exists")

    return user


# E1 - Register Package
@app.post("/packages", status_code=201)
def register_package(package: Package, token: str = Header(None)):
    function.authorize(token, function.EDIT)
    function.check_choice(package.status, function.STATUSES, "status")

    return function.add_package(
        name=package.name,
        destination=package.destination,
        weight=package.weight,
        arrival_date=str(package.arrival_date),
        status=package.status,
    )


# E2 - Get Package
@app.get("/packages/{package_id}")
def get_package(package_id: int, token: str = Header(None)):
    function.authorize(token, function.VIEW)

    package = function.get_package(package_id=package_id)

    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")

    return package


# E3 - Update Package
@app.patch("/packages/{package_id}")
def update_package(package_id: int, package: UpdatePackage, token: str = Header(None)):
    function.authorize(token, function.EDIT)
    function.check_choice(package.status, function.STATUSES, "status")

    fields = [package.name, package.destination, package.weight, package.arrival_date, package.status]
    if all(f is None for f in fields):
        raise HTTPException(status_code=422, detail="Provide at least one field to update")

    arrival_date = str(package.arrival_date) if package.arrival_date else None

    result = function.update_package(
        package_id=package_id,
        name=package.name,
        destination=package.destination,
        weight=package.weight,
        arrival_date=arrival_date,
        status=package.status,
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Package not found")

    return result


# E4 - Delete Package (admin only)
@app.delete("/packages/{package_id}")
def delete_package(package_id: int, token: str = Header(None)):
    function.authorize(token, function.ADMIN)

    result = function.delete_package(package_id)

    if result == "not_found":
        raise HTTPException(status_code=404, detail="Package not found")

    if result == "dispatched":
        raise HTTPException(status_code=409, detail="Cannot delete a dispatched package")

    return {"message": "Package deleted successfully"}


# E5 - Search Packages
@app.get("/packages")
def search_packages(
    destination: str = None,
    status: str = None,
    arrival_date: date = None,
    token: str = Header(None),
):
    function.authorize(token, function.VIEW)
    function.check_choice(status, function.STATUSES, "status")

    return function.get_packages(
        destination=destination,
        status=status,
        arrival_date=str(arrival_date) if arrival_date else None,
    )


# E6 - View Dispatch Batches
@app.get("/dispatches")
def view_batches(
    destination: str = None,
    vehicle: str = None,
    status: str = None,
    token: str = Header(None),
):
    function.authorize(token, function.VIEW)
    function.check_choice(status, function.BATCH_STATUSES, "status")

    return function.get_batches(destination=destination, vehicle=vehicle, status=status)


# E7 - Warehouse Summary
@app.get("/stats/dispatch-summary")
def warehouse_summary(token: str = Header(None)):
    function.authorize(token, function.VIEW)

    return function.get_summary()


# E8 - Create Dispatch Batch
@app.post("/dispatches", status_code=201)
def create_batch(dispatch: DispatchBatch, token: str = Header(None)):
    function.authorize(token, function.EDIT)
    function.check_choice(dispatch.status, function.BATCH_STATUSES, "status")

    result = function.create_batch(
        destination=dispatch.destination,
        vehicle=dispatch.vehicle,
        status=dispatch.status,
        package_ids=dispatch.package_ids,
    )

    if "error" in result:
        raise HTTPException(status_code=result["code"], detail=result["error"])

    return result

