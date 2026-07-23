from fastapi import FastAPI, HTTPException

from classes import Employee, Department

app = FastAPI(title="Employee Directory")


def build_directory():
    employees = Employee.load_all("class_reg.txt", "emp")
    departments = Department.load_all("class_reg.txt", "dept")
    dept_by_name = {dept.name: dept.department for dept in departments}
    return [
        {"name": emp.name, "status": emp.status, "department": dept_by_name.get(emp.name, "Unknown")}
        for emp in employees
    ]


@app.get("/employees")
def list_employees():
    return build_directory()


@app.get("/employees/{name}")
def get_employee(name: str):
    for emp in build_directory():
        if emp["name"] == name:
            return emp
    raise HTTPException(status_code=404, detail=f"Employee '{name}' not found")
