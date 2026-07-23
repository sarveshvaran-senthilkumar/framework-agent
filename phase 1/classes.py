import json


def _load_registry(filepath):
    with open(filepath, "r") as file:
        return json.load(file)


class Employee:
    def __init__(self, name, status):
        self.name = name
        self.status = status

    @staticmethod
    def load_all(filepath, key="emp"):
        data = _load_registry(filepath)[key]
        return [Employee(name, status) for name, status in data.items()]


class Department:
    def __init__(self, name, department):
        self.name = name
        self.department = department

    @staticmethod
    def load_all(filepath, key="dept"):
        data = _load_registry(filepath)[key]
        return [Department(name, department) for name, department in data.items()]
