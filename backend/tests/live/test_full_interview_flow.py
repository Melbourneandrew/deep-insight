"""
Long-running integration test for the complete interview flow.

Tests the entire process:
1. Create business
2. Add two questions  
3. Add employee
4. Start interview
5. Conduct full 6-question interview (2 base + 4 AI-generated follow-ups)
6. Verify interview completion

This test hits real endpoints and may use real LLM calls.
"""

import pytest
import time
from uuid import UUID
from typing import Dict, Any, Optional

from deep_insight_client import (
    BusinessesApi,
    QuestionsApi,
    EmployeesApi,
    Business,
    Question,
    Employee,
)


class TestFullInterviewFlow:
    """Integration test for complete interview workflow."""
    
    def setup_method(self):
        """Set up test data that will be created during the test."""
        self.business_id: Optional[UUID] = None
        self.employee_id: Optional[UUID] = None
        self.interview_id: Optional[UUID] = None
        self.question_ids: list[UUID] = []
        self.interview_responses: list[Dict[str, Any]] = []
    
    @pytest.mark.integration
    def test_complete_interview_flow(self, api_client):
        """Test the complete interview flow from business creation to completion."""
        
        # Create API instances using the fixture
        businesses_api = BusinessesApi(api_client)
        questions_api = QuestionsApi(api_client)
        employees_api = EmployeesApi(api_client)
        # Step 1: Create a business
        print("\n🏢 Step 1: Creating business...")
        business_data = Business(
            name="Test Interview Company"
        )
        
        created_business = businesses_api.create_business_businesses_post(business=business_data)
        self.business_id = UUID(str(created_business.id))
        print(f"✅ Created business: {self.business_id}")
            
        # Step 2: Add two base questions
        print("\n❓ Step 2: Adding base questions...")
        question_1_data = Question(
            content="Tell me about your experience with teamwork and collaboration.",
            business_id=str(self.business_id),
            is_follow_up=False
        )
        
        created_question_1 = questions_api.create_question_questions_post(question=question_1_data)
        question_1_id = UUID(str(created_question_1.id))
        self.question_ids.append(question_1_id)
        print(f"✅ Created question 1: {question_1_id}")
        
        question_2_data = Question(
            content="Describe a challenging project you worked on and how you overcame obstacles.",
            business_id=str(self.business_id),
            is_follow_up=False
        )
        
        created_question_2 = questions_api.create_question_questions_post(question=question_2_data)
        question_2_id = UUID(str(created_question_2.id))
        self.question_ids.append(question_2_id)
        print(f"✅ Created question 2: {question_2_id}")
            
        # Step 3: Add an employee
        print("\n👤 Step 3: Adding employee...")
        employee_data = Employee(
            email="test.employee@testcompany.com",
            bio="Test employee for interview flow",
            business_id=str(self.business_id)
        )
        
        created_employee = employees_api.create_employee_employees_post(employee=employee_data)
        self.employee_id = UUID(str(created_employee.id))
        print(f"✅ Created employee: {self.employee_id}")
            
        # Step 4: Start the interview
        print("\n🎯 Step 4: Starting interview...")
        interview_data = {
            "employee_id": str(self.employee_id)
        }
        
        response = client.post("/start-interview/", json=interview_data)
        assert response.status_code == 201
        interview_response = response.json()
        self.interview_id = UUID(interview_response["interview_id"])
        print(f"✅ Started interview: {self.interview_id}")
            
        # Step 5: Conduct the full interview (6 questions expected)
        print("\n💬 Step 5: Conducting full interview...")
        
        question_count = 0
        max_questions = 10  # Safety limit to prevent infinite loops
        
        while question_count < max_questions:
            question_count += 1
            print(f"\n--- Question {question_count} ---")
            
            # Get next question
            next_question_data = {
                "interview_id": str(self.interview_id)
            }
            
            response = client.post("/next-question/", json=next_question_data)
            assert response.status_code == 200
            
            next_question_response = response.json()
            
            # Check if interview is over
            if next_question_response["is_interview_over"]:
                print(f"🏁 Interview completed after {question_count - 1} questions")
                break
            
            # Get the question
            question = next_question_response["question"]
            assert question is not None
            question_id = UUID(question["id"])
            question_content = question["content"]
            
            print(f"📋 Question {question_count}: {question_content}")
            print(f"🆔 Question ID: {question_id}")
            print(f"🔧 Is follow-up: {question.get('is_follow_up', False)}")
            
            # Generate a realistic answer based on the question
            answer = self._generate_test_answer(question_content, question_count)
            print(f"💭 Answer: {answer}")
            
            # Submit the answer
            answer_data = {
                "interview_id": str(self.interview_id),
                "question_id": str(question_id),
                "content": answer
            }
            
            response = client.post("/answer-question/", json=answer_data)
            assert response.status_code == 201
            answer_response = response.json()
            assert answer_response["success"] is True
            
            # Store the Q&A for analysis
            self.interview_responses.append({
                "question_number": question_count,
                "question_id": str(question_id),
                "question_content": question_content,
                "is_follow_up": question.get("is_follow_up", False),
                "answer": answer
            })
            
            print("✅ Answer submitted successfully")
            
            # Small delay to be respectful to LLM API
            time.sleep(1)
            
        # Step 6: Verify the interview flow
        print("\n🔍 Step 6: Verifying interview structure...")
        
        # Should have exactly 6 questions (2 base + 4 AI follow-ups)
        expected_questions = 6
        actual_questions = len(self.interview_responses)
        
        print(f"Expected questions: {expected_questions}")
        print(f"Actual questions: {actual_questions}")
        
        assert actual_questions == expected_questions, f"Expected {expected_questions} questions, got {actual_questions}"
        
        # Verify the question pattern: base -> follow-up -> follow-up -> base -> follow-up -> follow-up
        expected_pattern = [False, True, True, False, True, True]  # False = base, True = follow-up
        actual_pattern = [q["is_follow_up"] for q in self.interview_responses]
        
        print(f"Expected pattern: {expected_pattern}")
        print(f"Actual pattern: {actual_pattern}")
        
        assert actual_pattern == expected_pattern, f"Question pattern mismatch. Expected {expected_pattern}, got {actual_pattern}"
        
        # Verify that we have exactly 2 base questions and 4 follow-ups
        base_questions = [q for q in self.interview_responses if not q["is_follow_up"]]
        follow_up_questions = [q for q in self.interview_responses if q["is_follow_up"]]
        
        assert len(base_questions) == 2, f"Expected 2 base questions, got {len(base_questions)}"
        assert len(follow_up_questions) == 4, f"Expected 4 follow-up questions, got {len(follow_up_questions)}"
        
        print("✅ Interview structure verified correctly!")
        
        # Step 7: Verify interview is actually complete
        print("\n🏁 Step 7: Verifying interview completion...")
        
        # Try to get next question - should indicate interview is over
        next_question_data = {
            "interview_id": str(self.interview_id)
        }
        
        response = client.post("/next-question/", json=next_question_data)
        assert response.status_code == 200
        
        final_response = response.json()
        assert final_response["is_interview_over"] is True
        assert final_response["question"] is None
        
        print("✅ Interview completion verified!")
        
        # Print summary
        print("\n📊 INTERVIEW FLOW SUMMARY:")
        print(f"Business ID: {self.business_id}")
        print(f"Employee ID: {self.employee_id}")
        print(f"Interview ID: {self.interview_id}")
        print(f"Total Questions: {len(self.interview_responses)}")
        print(f"Base Questions: {len(base_questions)}")
        print(f"AI Follow-ups: {len(follow_up_questions)}")
        
        print("\n📝 Question Flow:")
        for i, q in enumerate(self.interview_responses, 1):
            q_type = "AI Follow-up" if q["is_follow_up"] else "Base Question"
            print(f"  {i}. {q_type}: {q['question_content'][:60]}...")
        
        print("\n🎉 COMPLETE INTERVIEW FLOW TEST PASSED!")
    
    def _generate_test_answer(self, question: str, question_number: int) -> str:
        """Generate realistic test answers for different types of questions."""
        
        base_answers = {
            1: "I have extensive experience working in collaborative team environments. In my previous role, I worked closely with cross-functional teams including developers, designers, and product managers. I find that clear communication and regular check-ins are key to successful teamwork.",
            
            2: "One challenging project I worked on was implementing a new customer onboarding system. We faced technical constraints and tight deadlines. I overcame these by breaking down the project into smaller milestones, collaborating closely with stakeholders, and implementing agile methodologies.",
            
            3: "I believe effective teamwork starts with establishing clear roles and responsibilities. I always make sure to understand my team members' strengths and how I can best contribute to our shared goals.",
            
            4: "The main obstacle was integrating with legacy systems that had limited documentation. I tackled this by scheduling sessions with senior developers who had worked with those systems before and creating detailed documentation as we went.",
            
            5: "I learned that proactive communication prevents most team conflicts. I now schedule regular one-on-ones with team members to address any concerns early and ensure everyone feels heard.",
            
            6: "Next time, I would allocate more time upfront for research and planning. The pressure to deliver quickly led us to make some technical decisions that we had to revisit later, which ultimately cost more time."
        }
        
        return base_answers.get(question_number, f"This is a detailed response to question {question_number}. I would approach this by carefully considering all aspects and drawing from my professional experience to provide meaningful insights.")


if __name__ == "__main__":
    """Run the test manually for debugging."""
    print("To run this test manually, use pytest:")
    print("pytest backend/tests/live/test_full_interview_flow.py::TestFullInterviewFlow::test_complete_interview_flow -v -s")
