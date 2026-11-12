from fastapi import FastAPI, HTTPException

import functions 

app = FastAPI(title="Warehouse Dispatch Management System")


# E1: Register a package
@app.post("/packages", status_code=201)
def register_package(
    name: str, destination: str, weight: float, arrival_date: str, status: str = "pending"
):
    result = functions.register_package(name, destination, weight, arrival_date, status)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result

@app.post("/login")
def login(username: str, password:str):
    is_login = functions.verify_login(username=username, password=password)
    return {"login": is_login} 

