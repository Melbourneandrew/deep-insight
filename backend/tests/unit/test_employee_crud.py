"""
Comprehensive CRUD tests for Employee routes using the generated API client.

This module demonstrates how to use the generated deep_insight_client 
to perform Create, Read, Update, and Delete operations on Employee resources.
"""

import pytest
from uuid import UUID
from typing import List
from fastapi.testclient import TestClient
from datetime import datetime

from deep_insight_client import (
    EmployeesApi,
    BusinessesApi,
    Employee,
    Business,
    CreateBusinessRequest,
    ApiException,
)


@pytest.mark.integration
class TestEmployeeCRUD:
    """Test class for Employee CRUD operations using the generated API client."""

    def test_create_employee(
        self, employees_api: EmployeesApi, sample_employee_data: dict
    ):
        """Test creating a new employee through the API client."""
        from deep_insight_client import Employee

        # Create Employee object from sample data
        employee = Employee(**sample_employee_data)

        # Create the employee via API
        created_employee = employees_api.create_employee_employees_post(
            employee=employee
        )

        # Assertions
        assert created_employee is not None
        assert created_employee.id is not None
        assert isinstance(created_employee.id, (str, UUID))
        assert created_employee.email == sample_employee_data["email"]
        assert created_employee.bio == sample_employee_data["bio"]
        assert str(created_employee.business_id) == sample_employee_data["business_id"]

    def test_list_employees_empty(self, employees_api: EmployeesApi):
        """Test listing employees when none exist."""

        employees = employees_api.list_employees_employees_get()

        assert isinstance(employees, list)
        assert len(employees) == 0

    def test_list_employees_with_data(
        self, employees_api: EmployeesApi, sample_employee_data: dict
    ):
        """Test listing employees after creating some."""
        from deep_insight_client import Employee

        # Create multiple employees
        employee1 = Employee(**sample_employee_data)
        employee2 = Employee(
            **{**sample_employee_data, "email": "jane.doe@testcompany.com"}
        )

        created_employee1 = employees_api.create_employee_employees_post(
            employee=employee1
        )
        created_employee2 = employees_api.create_employee_employees_post(
            employee=employee2
        )

        # List all employees
        employees = employees_api.list_employees_employees_get()

        # Assertions
        assert isinstance(employees, list)
        assert len(employees) == 2

        employee_ids = [str(emp.id) for emp in employees]
        assert str(created_employee1.id) in employee_ids
        assert str(created_employee2.id) in employee_ids

    def test_list_employees_by_business_id(
        self, api_client, sample_employee_data: dict
    ):
        """Test filtering employees by business_id."""
        from deep_insight_client import EmployeesApi, BusinessesApi, Employee, Business

        # Create specific API instances inline
        employees_api = EmployeesApi(api_client)
        businesses_api = BusinessesApi(api_client)

        # Create a second business
        created_business2 = businesses_api.create_business_businesses_post(
            create_business_request=CreateBusinessRequest(
                name="Second Company"
            )
        )

        # Create employees for different businesses
        employee1 = Employee(**sample_employee_data)
        employee2 = Employee(
            **{
                **sample_employee_data,
                "email": "employee@secondcompany.com",
                "business_id": str(created_business2.id),
            }
        )

        created_employee1 = employees_api.create_employee_employees_post(
            employee=employee1
        )
        created_employee2 = employees_api.create_employee_employees_post(
            employee=employee2
        )

        # Filter by first business
        employees_business1 = employees_api.list_employees_employees_get(
            business_id=str(sample_employee_data["business_id"])
        )

        # Filter by second business
        employees_business2 = employees_api.list_employees_employees_get(
            business_id=created_business2.id
        )

        # Assertions
        assert len(employees_business1) == 1
        assert str(employees_business1[0].id) == str(created_employee1.id)

        # Second business will have 5 seeded employees + 1 created by test = 6 total
        assert len(employees_business2) == 6
        # Find our created employee among the results
        created_employee_ids = [str(emp.id) for emp in employees_business2]
        assert str(created_employee2.id) in created_employee_ids

    def test_get_employee_by_id(self, api_client, sample_employee_data: dict):
        """Test retrieving a specific employee by ID."""
        from deep_insight_client import EmployeesApi, Employee

        # Create specific API instance inline
        employees_api = EmployeesApi(api_client)

        # Create an employee
        employee = Employee(**sample_employee_data)
        created_employee = employees_api.create_employee_employees_post(
            employee=employee
        )

        # Retrieve the employee by ID
        retrieved_employee = employees_api.get_employee_employees_employee_id_get(
            employee_id=str(created_employee.id)
        )

        # Assertions
        assert retrieved_employee is not None
        assert str(retrieved_employee.id) == str(created_employee.id)
        assert retrieved_employee.email == created_employee.email
        assert retrieved_employee.bio == created_employee.bio
        assert str(retrieved_employee.business_id) == str(created_employee.business_id)

    def test_get_nonexistent_employee(self, api_client):
        """Test retrieving a non-existent employee returns 404."""
        from uuid import uuid4
        from deep_insight_client import EmployeesApi

        # Create specific API instance inline
        employees_api = EmployeesApi(api_client)

        non_existent_id = str(uuid4())

        with pytest.raises(ApiException) as exc_info:
            employees_api.get_employee_employees_employee_id_get(
                employee_id=non_existent_id
            )

        assert exc_info.value.status == 404
        assert "Employee not found" in str(exc_info.value)

    def test_update_employee(
        self, api_client, sample_employee_data: dict, updated_employee_data: dict
    ):
        """Test updating an existing employee."""
        from deep_insight_client import EmployeesApi, Employee

        # Create specific API instance inline
        employees_api = EmployeesApi(api_client)

        # Create an employee
        employee = Employee(**sample_employee_data)
        created_employee = employees_api.create_employee_employees_post(
            employee=employee
        )

        # Update the employee
        updated_employee = Employee(**updated_employee_data)
        response = employees_api.update_employee_employees_employee_id_put(
            employee_id=str(created_employee.id), employee=updated_employee
        )

        # Assertions
        assert response is not None
        assert str(response.id) == str(created_employee.id)
        assert response.email == updated_employee_data["email"]
        assert response.bio == updated_employee_data["bio"]

        # Verify the update persisted by fetching again
        retrieved_employee = employees_api.get_employee_employees_employee_id_get(
            employee_id=str(created_employee.id)
        )
        assert retrieved_employee.email == updated_employee_data["email"]
        assert retrieved_employee.bio == updated_employee_data["bio"]

    def test_update_nonexistent_employee(self, api_client, updated_employee_data: dict):
        """Test updating a non-existent employee returns 404."""
        from uuid import uuid4
        from deep_insight_client import EmployeesApi, Employee

        # Create specific API instance inline
        employees_api = EmployeesApi(api_client)

        non_existent_id = str(uuid4())
        updated_employee = Employee(**updated_employee_data)
        with pytest.raises(ApiException) as exc_info:
            employees_api.update_employee_employees_employee_id_put(
                employee_id=non_existent_id, employee=updated_employee
            )

        assert exc_info.value.status == 404
        assert "Employee not found" in str(exc_info.value)

    def test_delete_employee(self, api_client, sample_employee_data: dict):
        """Test deleting an employee."""
        from deep_insight_client import EmployeesApi, Employee

        # Create specific API instance inline
        employees_api = EmployeesApi(api_client)

        # Create an employee
        employee = Employee(**sample_employee_data)
        created_employee = employees_api.create_employee_employees_post(
            employee=employee
        )

        # Verify employee exists
        retrieved_employee = employees_api.get_employee_employees_employee_id_get(
            employee_id=str(created_employee.id)
        )
        assert retrieved_employee is not None

        # Delete the employee
        employees_api.delete_employee_employees_employee_id_delete(
            employee_id=str(created_employee.id)
        )

        # Verify employee no longer exists
        with pytest.raises(ApiException) as exc_info:
            employees_api.get_employee_employees_employee_id_get(
                employee_id=str(created_employee.id)
            )

        assert exc_info.value.status == 404
        assert "Employee not found" in str(exc_info.value)

    def test_delete_nonexistent_employee(self, employees_api: EmployeesApi):
        """Test deleting a non-existent employee returns 404."""
        from uuid import uuid4

        non_existent_id = uuid4()

        with pytest.raises(ApiException) as exc_info:
            employees_api.delete_employee_employees_employee_id_delete(
                employee_id=str(non_existent_id)
            )

        assert exc_info.value.status == 404
        assert "Employee not found" in str(exc_info.value)

    def test_full_crud_lifecycle(
        self,
        employees_api: EmployeesApi,
        sample_employee_data: dict,
        updated_employee_data: dict,
    ):
        """Test the complete CRUD lifecycle for an employee."""
        # 1. CREATE
        employee = Employee(**sample_employee_data)
        created_employee = employees_api.create_employee_employees_post(
            employee=employee
        )
        assert created_employee.email == sample_employee_data["email"]

        # 2. READ
        retrieved_employee = employees_api.get_employee_employees_employee_id_get(
            employee_id=str(created_employee.id)
        )
        assert str(retrieved_employee.id) == str(created_employee.id)

        # 3. UPDATE
        updated_employee = Employee(**updated_employee_data)
        updated_response = employees_api.update_employee_employees_employee_id_put(
            employee_id=str(created_employee.id), employee=updated_employee
        )
        assert updated_response.email == updated_employee_data["email"]

        # 4. DELETE
        employees_api.delete_employee_employees_employee_id_delete(
            employee_id=str(created_employee.id)
        )

        # 5. VERIFY DELETION
        with pytest.raises(ApiException) as exc_info:
            employees_api.get_employee_employees_employee_id_get(
                employee_id=str(created_employee.id)
            )
        assert exc_info.value.status == 404


@pytest.mark.unit
class TestEmployeeValidation:
    """Test employee data validation using the client models."""

    def test_employee_model_creation(self, test_business: Business):
        """Test creating an Employee model with valid data."""
        employee_data = {
            "email": "test@example.com",
            "bio": "Developer",
            "business_id": str(test_business.id),
            "created_at": datetime.now(),
        }

        employee = Employee(**employee_data)

        assert employee.email == "test@example.com"
        assert employee.bio == "Developer"
        assert str(employee.business_id) == str(test_business.id)

    def test_employee_model_with_id(self, test_business: Business):
        """Test creating an Employee model with an ID."""
        from uuid import uuid4

        employee_id = str(uuid4())
        employee_data = {
            "id": employee_id,
            "email": "test@example.com",
            "bio": "Developer",
            "business_id": str(test_business.id),
            "created_at": datetime.now(),
        }

        employee = Employee(**employee_data)

        assert employee.id == employee_id
        assert employee.email == "test@example.com"
        assert employee.bio == "Developer"
