"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ConfirmDelete } from "@/components/ConfirmDelete";
import { AddEmployeeModal } from "@/components/AddEmployeeModal";
import { AddQuestionModal } from "@/components/AddQuestionModal";
import { Trash2, Plus, Play } from "lucide-react";
import { api } from "@/lib/api";
import { StartInterviewsModal } from "./StartInterviewsModal";

interface Business {
  id: string;
  name: string;
}

interface Employee {
  id: string;
  email: string;
  bio?: string;
  business_id: string;
}

interface Question {
  id: string;
  content: string;
  is_follow_up: boolean;
  business_id: string;
}

export default function BusinessDetailsPage() {
  const params = useParams();
  const businessId = params.business_id as string;

  const [business, setBusiness] = useState<Business | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showAddEmployee, setShowAddEmployee] = useState(false);
  const [showAddQuestion, setShowAddQuestion] = useState(false);
  const [showStartInterviews, setShowStartInterviews] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<{
    type: "employee" | "question";
    id: string;
    name: string;
  } | null>(null);

  // Load data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [businessResponse, employeesResponse, questionsResponse] =
          await Promise.all([
            api.businesses.get(businessId),
            api.employees.list(businessId),
            api.questions.list(businessId),
          ]);

        if (!businessResponse.ok) {
          throw new Error("Failed to load business");
        }
        if (!employeesResponse.ok) {
          throw new Error("Failed to load employees");
        }
        if (!questionsResponse.ok) {
          throw new Error("Failed to load questions");
        }

        const businessData = await businessResponse.json();
        const employeesData = await employeesResponse.json();
        const questionsData = await questionsResponse.json();

        setBusiness(businessData);
        setEmployees(employeesData);
        // Filter out follow-up questions
        setQuestions(questionsData.filter((q: Question) => !q.is_follow_up));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    if (businessId) {
      loadData();
    }
  }, [businessId]);

  // Add employee
  const handleAddEmployee = async (employeeData: {
    email: string;
    bio?: string;
  }) => {
    const response = await api.employees.create({
      ...employeeData,
      business_id: businessId,
    });

    if (!response.ok) {
      throw new Error("Failed to add employee");
    }

    const newEmployee = await response.json();
    setEmployees((prev) => [...prev, newEmployee]);
  };

  // Add question
  const handleAddQuestion = async (questionData: {
    content: string;
    is_follow_up?: boolean;
  }) => {
    const response = await api.questions.create({
      ...questionData,
      business_id: businessId,
    });

    if (!response.ok) {
      throw new Error("Failed to add question");
    }

    const newQuestion = await response.json();
    setQuestions((prev) => [...prev, newQuestion]);
  };

  // Delete employee
  const handleDeleteEmployee = async (employeeId: string) => {
    const response = await api.employees.delete(employeeId);

    if (!response.ok) {
      throw new Error("Failed to delete employee");
    }

    setEmployees((prev) => prev.filter((emp) => emp.id !== employeeId));
  };

  // Delete question
  const handleDeleteQuestion = async (questionId: string) => {
    const response = await api.questions.delete(questionId);

    if (!response.ok) {
      throw new Error("Failed to delete question");
    }

    setQuestions((prev) => prev.filter((q) => q.id !== questionId));
  };

  // Handle confirm delete
  const handleConfirmDelete = async () => {
    if (!confirmDelete) return;

    if (confirmDelete.type === "employee") {
      await handleDeleteEmployee(confirmDelete.id);
    } else {
      await handleDeleteQuestion(confirmDelete.id);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-gray-600">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">Error: {error}</div>
        </div>
      </div>
    );
  }

  if (!business) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-gray-600">Business not found</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Business Name Header */}
      <div className="mb-8 flex justify-between items-end">
        <div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
            BUSINESS
          </div>
          <h1 className="text-3xl font-bold text-gray-900">{business.name}</h1>
        </div>
        <Button onClick={() => setShowStartInterviews(true)}>
          <Play className="w-4 h-4 mr-2" />
          Start Interviews
        </Button>
      </div>

      {/* Side-by-side Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Employees Table */}
        <div className="">
          <div className="py-4 px-2 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">Employees</h2>
            <Button onClick={() => setShowAddEmployee(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add Employee
            </Button>
          </div>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {employees.length === 0 ? (
                  <tr>
                    <td
                      colSpan={2}
                      className="px-6 py-4 text-center text-gray-500"
                    >
                      No employees found
                    </td>
                  </tr>
                ) : (
                  employees.map((employee) => (
                    <tr key={employee.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {employee.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setConfirmDelete({
                              type: "employee",
                              id: employee.id,
                              name: employee.email,
                            })
                          }
                          className="text-gray-500 hover:text-gray-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Questions Table */}
        <div className="">
          <div className="py-4 px-2 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">Questions</h2>
            <Button onClick={() => setShowAddQuestion(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create Question
            </Button>
          </div>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Question
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {questions.length === 0 ? (
                  <tr>
                    <td
                      colSpan={3}
                      className="px-6 py-4 text-center text-gray-500"
                    >
                      No questions found
                    </td>
                  </tr>
                ) : (
                  questions.map((question) => (
                    <tr key={question.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {question.content}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            question.is_follow_up
                              ? "bg-blue-100 text-blue-800"
                              : "bg-green-100 text-green-800"
                          }`}
                        >
                          {question.is_follow_up ? "Follow-up" : "Primary"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setConfirmDelete({
                              type: "question",
                              id: question.id,
                              name: question.content,
                            })
                          }
                          className="text-gray-500 hover:text-gray-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modals */}
      <AddEmployeeModal
        isOpen={showAddEmployee}
        onClose={() => setShowAddEmployee(false)}
        onAdd={handleAddEmployee}
      />

      <AddQuestionModal
        isOpen={showAddQuestion}
        onClose={() => setShowAddQuestion(false)}
        onAdd={handleAddQuestion}
      />

      <StartInterviewsModal
        isOpen={showStartInterviews}
        onClose={() => setShowStartInterviews(false)}
        businessId={businessId}
      />

      <ConfirmDelete
        isOpen={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleConfirmDelete}
        title={`Delete ${
          confirmDelete?.type === "employee" ? "Employee" : "Question"
        }`}
        description={`Are you sure you want to delete this ${confirmDelete?.type}? This action cannot be undone.`}
        itemName={confirmDelete?.name}
      />
    </div>
  );
}
