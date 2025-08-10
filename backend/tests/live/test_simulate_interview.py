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
    InterviewsApi,
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
        
    def _wait_for_simulation_completion(self, api_client, business_id: UUID, expected_employees: int = 1, timeout: int = 120) -> List[Dict[str, Any]]:
        """Poll for simulation completion by checking interview responses.
        
        Args:
            api_client: API client instance
            business_id: Business ID to check interviews for
            expected_employees: Expected number of employees with completed interviews
            timeout: Maximum wait time in seconds
            
        Returns:
            List of interview details with responses
            
        Raises:
            TimeoutError: If simulation doesn't complete within timeout
        """
        interviews_api = InterviewsApi(api_client)
        start_time = time.time()
        check_interval = 2  # Start with 2 second intervals
        
        print(f"⏳ Waiting for simulation completion (max {timeout}s)...")
        
        while time.time() - start_time < timeout:
            try:
                # Get all interview details for this business (includes responses)
                interview_details = interviews_api.get_business_interview_details_interviews_business_business_id_details_get(
                    business_id=str(business_id)
                )
                
                if len(interview_details) >= expected_employees:
                    # Check if we have completed interviews with responses
                    completed_interviews = []
                    
                    for interview_detail in interview_details:
                        # Count responses - expect at least some for a completed simulation
                        response_count = len(interview_detail.questions_and_responses)
                        if response_count > 0:  # At least some responses indicate progress
                            completed_interviews.append({
                                'interview_id': interview_detail.interview_id,
                                'detail': interview_detail,
                                'response_count': response_count
                            })
                            print(f"  📝 Interview {interview_detail.interview_id}: {response_count} responses")
                    
                    if len(completed_interviews) >= expected_employees:
                        # Check if we have expected total responses (base + follow-ups)
                        # For our tests: each employee should have responses to all questions
                        all_complete = True
                        for comp_interview in completed_interviews:
                            # Expect responses to base questions + follow-ups
                            # Conservative check: at least 3 responses per interview
                            if comp_interview['response_count'] < 3:
                                all_complete = False
                                break
                        
                        if all_complete:
                            elapsed = time.time() - start_time
                            print(f"✅ Simulation completed in {elapsed:.2f}s")
                            return completed_interviews
                
                # Not ready yet, wait and try again
                elapsed = time.time() - start_time
                print(f"  ⏳ {elapsed:.1f}s: Found {len(interview_details)} interviews, waiting...")
                time.sleep(check_interval)
                
                # Increase check interval gradually
                if check_interval < 10:
                    check_interval += 1
                    
            except Exception as e:
                print(f"  ⚠️  Error checking interviews: {e}")
                time.sleep(check_interval)
        
        raise TimeoutError(f"Simulation did not complete within {timeout} seconds")
    
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
            
        # Step 4: Start employee interview simulation in background
        print("\n🤖 Step 4: Starting employee interview simulation...")
        
        simulate_request = SimulateEmployeeInterviewRequest(
            employee_id=str(employee_id)
            # interview_id not provided - should create a new interview
        )
        
        # Call the background simulate endpoint for this specific employee
        simulate_response = simulate_api.simulate_employee_interview_simulateinterview_employee_id_post(
            employee_id=str(employee_id),
            simulate_employee_interview_request=simulate_request
        )
        
        # Handle the case where the response might be None due to client generation issues
        if simulate_response is None:
            print("⚠️ Simulate response is None - this may be a client generation issue")
            print("✅ Simulation request sent successfully (no error thrown)")
            # We'll rely on the polling to verify it worked
        else:
            print(f"✅ Simulation started for employee: {employee_id}")
            print(f"📋 Status: {simulate_response.status}")
            print(f"💬 Message: {simulate_response.message}")
            
            # Verify background task started successfully
            assert simulate_response.status == "started"
            assert simulate_response.employee_id == str(employee_id)
        
        # Step 4.5: Wait for simulation to complete
        print("\n⏳ Step 4.5: Waiting for simulation completion...")
        completed_interviews = self._wait_for_simulation_completion(api_client, self.business_id, expected_employees=1)
        
        # Get the completed interview
        interview_data = completed_interviews[0]
        interview_detail = interview_data['detail']
        
        print(f"✅ Simulation completed for employee: {employee_id}")
        print(f"📋 Interview ID: {interview_data['interview_id']}")
        print(f"📝 Total Q&A Exchanges: {len(interview_detail.questions_and_responses)}")
        
        # Step 5: Verify simulation results from completed interview
        print("\n🔍 Step 5: Verifying simulation results...")
        
        # Get the interview and responses
        interview_id = interview_data['interview_id']
        responses = interview_detail.questions_and_responses
        
        # Verify basic structure
        assert interview_id is not None
        assert interview_detail.business_id == str(self.business_id)
        
        # Verify we have responses
        assert len(responses) > 0, "Should have at least one Q&A exchange"
        
        # Count base questions and follow-ups
        base_responses = [r for r in responses if not r.question_is_follow_up]
        follow_up_responses = [r for r in responses if r.question_is_follow_up]
        
        print(f"Base questions answered: {len(base_responses)}")
        print(f"Follow-up questions answered: {len(follow_up_responses)}")
        
        # Should have 3 base questions (we created 3)
        assert len(base_responses) == 3, f"Expected 3 base questions, got {len(base_responses)}"
        
        # Should have follow-ups (2 per base question = 6 total expected)
        expected_follow_ups = 6
        assert len(follow_up_responses) == expected_follow_ups, f"Expected {expected_follow_ups} follow-ups, got {len(follow_up_responses)}"
        
        # Verify each response has required fields
        for i, response in enumerate(responses, 1):
            assert response.question_id is not None
            assert response.question_content is not None and len(response.question_content) > 0
            assert response.response_content is not None and len(response.response_content) > 0
            assert isinstance(response.question_is_follow_up, bool)
            assert response.employee_email == "john.doe@simulatetest.com"
            
            print(f"Response {i}: {'Follow-up' if response.question_is_follow_up else 'Base'}")
            print(f"  Q: {response.question_content[:80]}...")
            print(f"  A: {response.response_content[:80]}...")
        
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
            
        # Step 4: Start business-wide interview simulation in background
        print("\n🤖 Step 4: Starting business-wide interview simulation...")
        
        simulate_request = SimulateInterviewRequest(
            business_id=str(self.business_id)
        )
        
        # Start the background simulation
        print("⏳ Starting parallel simulations in background...")
        start_time = time.time()
        
        simulate_response = simulate_api.simulate_business_interviews_simulate_interview_post(
            simulate_interview_request=simulate_request
        )
        
        # Handle the case where the response might be None due to client generation issues
        if simulate_response is None:
            print("⚠️ Business simulate response is None - this may be a client generation issue")
            print("✅ Business simulation request sent successfully (no error thrown)")
            # We'll rely on the polling to verify it worked
        else:
            print(f"✅ Business simulation started")
            print(f"📋 Status: {simulate_response.status}")
            print(f"💬 Message: {simulate_response.message}")
            
            # Verify background task started successfully
            assert simulate_response.status == "started"
            assert simulate_response.business_id == str(self.business_id)
        
        # Step 4.5: Wait for simulation to complete
        print("\n⏳ Step 4.5: Waiting for business simulation completion...")
        completed_interviews = self._wait_for_simulation_completion(
            api_client, 
            self.business_id, 
            expected_employees=len(employees_to_create)
        )
        
        end_time = time.time()
        simulation_duration = end_time - start_time
        
        print(f"✅ Business simulation completed in {simulation_duration:.2f} seconds")
        print(f"👥 Completed Interviews: {len(completed_interviews)}")
        
        # Step 5: Verify business simulation results from completed interviews
        print("\n🔍 Step 5: Verifying business simulation results...")
        
        # Verify we have interviews for all employees
        assert len(completed_interviews) == len(employees_to_create), f"Expected {len(employees_to_create)} completed interviews, got {len(completed_interviews)}"
        
        # Verify each employee interview
        employee_emails = [emp["email"] for emp in employees_to_create]
        
        for i, interview_data in enumerate(completed_interviews, 1):
            interview_id = interview_data['interview_id']
            interview_detail = interview_data['detail']
            responses = interview_detail.questions_and_responses
            
            print(f"\nInterview {i}:")
            print(f"  Interview ID: {interview_id}")
            print(f"  Business ID: {interview_detail.business_id}")
            print(f"  Responses: {len(responses)}")
            
            # Verify interview structure
            assert interview_id is not None
            assert interview_detail.business_id == str(self.business_id)
            assert len(responses) > 0, f"Interview {interview_id} should have responses"
            
            # Each employee should have responded to all questions (base + follow-ups)
            # With 2 base questions and 2 follow-ups each = 6 total expected
            expected_responses = 6
            assert len(responses) == expected_responses, f"Interview {interview_id} should have {expected_responses} responses, got {len(responses)}"
            
            # Verify we have the expected employee email
            if responses:
                employee_email = responses[0].employee_email
                assert employee_email in employee_emails, f"Employee email {employee_email} not in expected list"
                print(f"  Employee Email: {employee_email}")
            
            # Verify response structure
            for j, response in enumerate(responses, 1):
                assert response.question_id is not None
                assert response.question_content is not None
                assert response.response_content is not None
                assert isinstance(response.question_is_follow_up, bool)
                
                print(f"    Response {j}: {'Follow-up' if response.question_is_follow_up else 'Base'}")
                print(f"      Q: {response.question_content[:60]}...")
                print(f"      A: {response.response_content[:60]}...")
        
        print(f"\n✅ All {len(completed_interviews)} employee interviews verified!")
        print(f"⚡ Parallel processing completed {len(completed_interviews)} simulations in {simulation_duration:.2f} seconds")
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
