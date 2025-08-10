"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { api, StartInterviewResponse } from "@/lib/api";

interface Business {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

interface Employee {
  id: string;
  email: string;
  bio?: string;
  business_id: string;
  created_at: string;
  updated_at: string;
}

export default function StartInterviewPage() {
  const params = useParams();
  const router = useRouter();
  const business_id = params.business_id as string;

  const [business, setBusiness] = useState<Business | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Fetch business details
        const businessResponse = await api.businesses.get(business_id);
        if (!businessResponse.ok) {
          throw new Error("Failed to fetch business details");
        }
        const businessData = await businessResponse.json();
        setBusiness(businessData);

        // Fetch employees for this business
        const employeesResponse = await api.employees.list(business_id);
        if (!employeesResponse.ok) {
          throw new Error("Failed to fetch employees");
        }
        const employeesData = await employeesResponse.json();
        setEmployees(employeesData);

        // Select a random employee
        if (employeesData.length > 0) {
          const randomIndex = Math.floor(Math.random() * employeesData.length);
          setSelectedEmployee(employeesData[randomIndex]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setIsLoading(false);
      }
    };

    if (business_id) {
      fetchData();
    }
  }, [business_id]);

  const handleStartInterview = async () => {
    if (!selectedEmployee) {
      setError("No employee selected");
      return;
    }

    try {
      setIsStarting(true);
      setError(null);

      const response = await api.procedures.startInterview({
        employee_id: selectedEmployee.id,
      });

      if (!response.ok) {
        throw new Error("Failed to start interview");
      }

      const data: StartInterviewResponse = await response.json();
      console.log(data);

      // Navigate to the employee interview page
      router.push(
        `/businesses/${business_id}/interview/${data.interview_id}/employee/${selectedEmployee.id}`
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start interview"
      );
    } finally {
      setIsStarting(false);
    }
  };

  const handleSelectDifferentEmployee = () => {
    if (employees.length > 0) {
      const currentIndex = employees.findIndex(
        (emp) => emp.id === selectedEmployee?.id
      );
      const nextIndex = (currentIndex + 1) % employees.length;
      setSelectedEmployee(employees[nextIndex]);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading interview details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
            <h2 className="text-red-800 font-semibold mb-2">Error</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={() => window.location.reload()} variant="outline">
              Try Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!business || !selectedEmployee) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">No data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-10 bg-gray-50 flex items-center justify-center">
      <div className="max-w-2xl w-full">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Welcome to Your Interview
            </h1>
            <p className="text-lg text-gray-600 mb-6">
              You will be asked a few questions about your role at <br />
              <span className="font-semibold text-blue-600">
                {business.name}
              </span>
              .
            </p>
          </div>

          <div className="border rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              Interview Participant
            </h2>
            <div className="text-left flex items-center gap-2 justify-between">
              <p className="text-gray-700 mb-2">
                <span className="font-bold">{selectedEmployee.email}</span>
              </p>
              {employees.length > 1 && (
                <Button
                  onClick={handleSelectDifferentEmployee}
                  variant="outline"
                  size="sm"
                  disabled={isStarting}
                >
                  Change
                </Button>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <p className="text-gray-600">
              The interview will consist of several questions designed to
              understand your experience and perspective. Please answer honestly
              and thoughtfully.
            </p>

            <div className="pt-4">
              <Button
                onClick={handleStartInterview}
                disabled={isStarting}
                size="lg"
                className="px-8 py-3 text-lg"
              >
                {isStarting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Starting Interview...
                  </>
                ) : (
                  "Lets Begin"
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
