"""
Integration test for the simulate interview functionality.

Tests both individual employee simulation and business-wide simulation:
1. Create business with employees and questions
2. Test individual employee simulation (/simulate/{employee_id})
3. Test business-wide simulation (/simulate/)
4. Verify simulation results and interview completion

This test hits real endpoints and may use real LLM calls.
"""

import pytest
import time
from uuid import UUID
from typing import Dict, Any, Optional, List

from deep_insight_client import (
    BusinessesApi,
    CreateBusinessRequest,
    BusinessSeedData,
    QuestionsApi,
    EmployeesApi,
    ProceduresApi,
    Business,
    Question,
    Employee,
    SimulateApi,
    SimulateInterviewRequest,
    SimulateEmployeeInterviewRequest,
)


class TestSimulateInterview:
    """Integration test for simulate interview functionality."""
    
    def setup_method(self):
        """Set up test data that will be created during the test."""
        self.business_id: Optional[UUID] = None
        self.employee_ids: List[UUID] = []
        self.question_ids: List[UUID] = []
    
    @pytest.mark.integration
    def test_simulate_employee_interview(self, api_client):
        """Test simulating a single employee's interview."""
        
        # Create API instances using the fixture
        businesses_api = BusinessesApi(api_client)
        questions_api = QuestionsApi(api_client)
        employees_api = EmployeesApi(api_client)
        procedures_api = ProceduresApi(api_client)
        simulate_api = SimulateApi(api_client)
        
        # Step 1: Create a business with empty seed data
        print("\n🏢 Step 1: Creating business...")
        
        empty_seed_data = BusinessSeedData(employees=[], questions=[])
        created_business = businesses_api.create_business_businesses_post(
            create_business_request=CreateBusinessRequest(
                name="Simulate Test Company",
                seed_data=empty_seed_data
            )
        )
        self.business_id = UUID(str(created_business.id))
        print(f"✅ Created business: {self.business_id}")
            
        # Step 2: Add base questions
        print("\n❓ Step 2: Adding base questions...")
        
        questions_to_create = [
            "Tell me about your professional background and experience.",
            "What are your greatest strengths as a team member?",
            "Describe a challenging situation you handled recently."
        ]
        
        for i, question_content in enumerate(questions_to_create, 1):
            question_data = Question(
                content=question_content,
                business_id=str(self.business_id),
                is_follow_up=False
            )
            
            created_question = questions_api.create_question_questions_post(question=question_data)
            question_id = UUID(str(created_question.id))
            self.question_ids.append(question_id)
            print(f"✅ Created question {i}: {question_id}")
        
        print(f"✅ Created {len(questions_to_create)} base questions total")
            
        # Step 3: Add an employee with detailed bio
        print("\n👤 Step 3: Adding employee...")
        employee_data = Employee(
            email="john.doe@simulatetest.com",
            bio="Senior software engineer with 5 years of experience in full-stack development. Specializes in Python, React, and cloud infrastructure. Led multiple successful projects and mentors junior developers.",
            business_id=str(self.business_id)
        )
        
        created_employee = employees_api.create_employee_employees_post(employee=employee_data)
        employee_id = UUID(str(created_employee.id))
        self.employee_ids.append(employee_id)
        print(f"✅ Created employee: {employee_id}")
            
        # Step 4: Simulate the employee's interview (without providing interview_id - should create new)
        print("\n🤖 Step 4: Simulating employee interview...")
        
        simulate_request = SimulateEmployeeInterviewRequest(
            employee_id=str(employee_id)
            # interview_id not provided - should create a new interview
        )
        
        # Call the simulate endpoint for this specific employee
        simulate_response = simulate_api.simulate_employee_interview_simulateinterview_employee_id_post(
            employee_id=str(employee_id),
            simulate_employee_interview_request=simulate_request
        )
        
        print(f"✅ Simulation completed for employee: {employee_id}")
        print(f"📋 Interview ID: {simulate_response.interview_id}")
        print(f"👤 Employee Email: {simulate_response.employee_email}")
        print(f"🏢 Business: {simulate_response.business_name}")
        print(f"✅ Interview Complete: {simulate_response.is_interview_complete}")
        print(f"📝 Total Q&A Exchanges: {len(simulate_response.simulated_exchanges)}")
        
        # Step 5: Verify simulation results
        print("\n🔍 Step 5: Verifying simulation results...")
        
        # Verify basic response structure
        assert simulate_response.interview_id is not None
        assert simulate_response.employee_id == str(employee_id)
        assert simulate_response.employee_email == "john.doe@simulatetest.com"
        assert simulate_response.business_id == str(self.business_id)
        assert simulate_response.business_name == "Simulate Test Company"
        assert simulate_response.is_interview_complete is True
        
        # Verify we have simulated exchanges
        exchanges = simulate_response.simulated_exchanges
        assert len(exchanges) > 0, "Should have at least one Q&A exchange"
        
        # Count base questions and follow-ups
        base_exchanges = [e for e in exchanges if not e.is_follow_up]
        follow_up_exchanges = [e for e in exchanges if e.is_follow_up]
        
        print(f"Base questions answered: {len(base_exchanges)}")
        print(f"Follow-up questions answered: {len(follow_up_exchanges)}")
        
        # Should have 3 base questions (we created 3)
        assert len(base_exchanges) == 3, f"Expected 3 base questions, got {len(base_exchanges)}"
        
        # Should have follow-ups (2 per base question = 6 total expected)
        expected_follow_ups = 6
        assert len(follow_up_exchanges) == expected_follow_ups, f"Expected {expected_follow_ups} follow-ups, got {len(follow_up_exchanges)}"
        
        # Verify each exchange has required fields
        for i, exchange in enumerate(exchanges, 1):
            assert exchange.question_id is not None
            assert exchange.question_content is not None and len(exchange.question_content) > 0
            assert exchange.response_content is not None and len(exchange.response_content) > 0
            assert isinstance(exchange.is_follow_up, bool)
            
            print(f"Exchange {i}: {'Follow-up' if exchange.is_follow_up else 'Base'}")
            print(f"  Q: {exchange.question_content[:80]}...")
            print(f"  A: {exchange.response_content[:80]}...")
        
        print("✅ Employee simulation verification completed!")
        
    @pytest.mark.integration  
    def test_simulate_business_interviews(self, api_client):
        """Test simulating interviews for all employees in a business."""
        
        # Create API instances using the fixture
        businesses_api = BusinessesApi(api_client)
        questions_api = QuestionsApi(api_client)
        employees_api = EmployeesApi(api_client)
        procedures_api = ProceduresApi(api_client)
        simulate_api = SimulateApi(api_client)
        
        # Step 1: Create a business with empty seed data
        print("\n🏢 Step 1: Creating business for multi-employee simulation...")
        
        empty_seed_data = BusinessSeedData(employees=[], questions=[])
        created_business = businesses_api.create_business_businesses_post(
            create_business_request=CreateBusinessRequest(
                name="Multi-Employee Test Company",
                seed_data=empty_seed_data
            )
        )
        self.business_id = UUID(str(created_business.id))
        print(f"✅ Created business: {self.business_id}")
            
        # Step 2: Add base questions
        print("\n❓ Step 2: Adding base questions...")
        
        questions_to_create = [
            "What motivates you in your work?",
            "How do you handle stress and deadlines?"
        ]
        
        for i, question_content in enumerate(questions_to_create, 1):
            question_data = Question(
                content=question_content,
                business_id=str(self.business_id),
                is_follow_up=False
            )
            
            created_question = questions_api.create_question_questions_post(question=question_data)
            question_id = UUID(str(created_question.id))
            self.question_ids.append(question_id)
            print(f"✅ Created question {i}: {question_id}")
        
        print(f"✅ Created {len(questions_to_create)} base questions total")
            
        # Step 3: Add multiple employees with different bios
        print("\n👥 Step 3: Adding multiple employees...")
        
        employees_to_create = [
            {
                "email": "alice.smith@multitest.com",
                "bio": "Product manager with 3 years of experience in agile methodologies and cross-functional team leadership."
            },
            {
                "email": "bob.johnson@multitest.com", 
                "bio": "Frontend developer specializing in React and UX design, passionate about creating user-friendly interfaces."
            },
            {
                "email": "carol.williams@multitest.com",
                "bio": "Data scientist with expertise in machine learning and statistical analysis, focused on business intelligence."
            }
        ]
        
        for i, emp_data in enumerate(employees_to_create, 1):
            employee_data = Employee(
                email=emp_data["email"],
                bio=emp_data["bio"],
                business_id=str(self.business_id)
            )
            
            created_employee = employees_api.create_employee_employees_post(employee=employee_data)
            employee_id = UUID(str(created_employee.id))
            self.employee_ids.append(employee_id)
            print(f"✅ Created employee {i}: {employee_id} ({emp_data['email']})")
        
        print(f"✅ Created {len(employees_to_create)} employees total")
            
        # Step 4: Simulate interviews for all employees in business
        print("\n🤖 Step 4: Simulating business-wide interviews...")
        
        simulate_request = SimulateInterviewRequest(
            business_id=str(self.business_id)
        )
        
        # This should run simulations for all employees in parallel
        print("⏳ Running parallel simulations (this may take a moment)...")
        start_time = time.time()
        
        simulate_response = simulate_api.simulate_business_interviews_simulate_interview_post(
            simulate_interview_request=simulate_request
        )
        
        end_time = time.time()
        simulation_duration = end_time - start_time
        
        print(f"✅ Business simulation completed in {simulation_duration:.2f} seconds")
        print(f"📋 Main Interview ID: {simulate_response.interview_id}")
        print(f"🏢 Business: {simulate_response.business_name}")
        print(f"👥 Employee Simulations: {len(simulate_response.employee_simulations)}")
        
        # Step 5: Verify business simulation results
        print("\n🔍 Step 5: Verifying business simulation results...")
        
        # Verify basic response structure
        assert simulate_response.interview_id is not None
        assert simulate_response.business_id == str(self.business_id)
        assert simulate_response.business_name == "Multi-Employee Test Company"
        
        # Verify we have simulations for all employees
        employee_simulations = simulate_response.employee_simulations
        assert len(employee_simulations) == len(employees_to_create), f"Expected {len(employees_to_create)} employee simulations, got {len(employee_simulations)}"
        
        # Verify questions asked
        questions_asked = simulate_response.questions_asked
        assert len(questions_asked) == len(questions_to_create), f"Expected {len(questions_to_create)} questions, got {len(questions_asked)}"
        
        # Verify each employee simulation
        for i, emp_sim in enumerate(employee_simulations, 1):
            print(f"\nEmployee Simulation {i}:")
            print(f"  Employee ID: {emp_sim.employee_id}")
            print(f"  Email: {emp_sim.employee_email}")
            print(f"  Responses: {len(emp_sim.responses)}")
            
            # Verify employee simulation structure
            assert emp_sim.employee_id is not None
            assert emp_sim.employee_email is not None
            assert len(emp_sim.responses) > 0, f"Employee {emp_sim.employee_email} should have responses"
            
            # Each employee should have responded to all questions (base + follow-ups)
            # With 2 base questions and 2 follow-ups each = 6 total expected
            expected_responses = 6
            assert len(emp_sim.responses) == expected_responses, f"Employee {emp_sim.employee_email} should have {expected_responses} responses, got {len(emp_sim.responses)}"
            
            # Verify response structure
            for j, response in enumerate(emp_sim.responses, 1):
                assert response.get("question_id") is not None
                assert response.get("question_content") is not None
                assert response.get("response_content") is not None
                assert isinstance(response.get("is_follow_up"), bool)
                
                print(f"    Response {j}: {'Follow-up' if response['is_follow_up'] else 'Base'}")
                print(f"      Q: {response['question_content'][:60]}...")
                print(f"      A: {response['response_content'][:60]}...")
        
        print(f"\n✅ All {len(employee_simulations)} employee simulations verified!")
        print(f"⚡ Parallel processing completed {len(employee_simulations)} simulations in {simulation_duration:.2f} seconds")
        print("🎉 BUSINESS-WIDE SIMULATION TEST PASSED!")


if __name__ == "__main__":
    """Run the test manually for debugging."""
    print("To run individual employee simulation test:")
    print("pytest backend/tests/live/test_simulate_interview.py::TestSimulateInterview::test_simulate_employee_interview -v -s")
    print()
    print("To run business-wide simulation test:")
    print("pytest backend/tests/live/test_simulate_interview.py::TestSimulateInterview::test_simulate_business_interviews -v -s")
    print()
    print("To run all simulation tests:")
    print("pytest backend/tests/live/test_simulate_interview.py -v -s")
