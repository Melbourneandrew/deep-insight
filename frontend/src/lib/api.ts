const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types for business creation
export interface EmployeeSeedData {
  email: string;
  bio?: string;
}

export interface QuestionSeedData {
  content: string;
  is_follow_up?: boolean;
}

export interface BusinessSeedData {
  employees?: EmployeeSeedData[];
  questions?: QuestionSeedData[];
}

export interface CreateBusinessRequest {
  name: string;
  seed_data?: BusinessSeedData;
}

// Types for interview procedures
export interface NextQuestionRequest {
  interview_id: string;
}

export interface Question {
  id: string;
  content: string;
  is_follow_up: boolean;
  business_id: string;
}

export interface NextQuestionResponse {
  question?: Question;
  is_interview_over: boolean;
}

export interface AnswerQuestionRequest {
  interview_id: string;
  question_id: string;
  content: string;
}

export interface AnswerQuestionResponse {
  success: boolean;
  interview_id: string;
}

// Types for starting interviews
export interface StartInterviewRequest {
  employee_id: string;
}

export interface StartInterviewResponse {
  interview_id: string;
}

// Types for interview simulation
export interface SimulateInterviewRequest {
  business_id: string;
}

export interface EmployeeSimulation {
  employee_id: string;
  employee_email: string;
  responses: Array<{
    question_id: string;
    question_content: string;
    response_content: string;
    is_follow_up: boolean;
  }>;
}

export interface SimulateInterviewResponse {
  interview_id: string;
  business_id: string;
  business_name: string;
  employee_simulations: EmployeeSimulation[];
  questions_asked: Array<{
    question_id: string;
    content: string;
    is_follow_up: boolean;
    order_index?: number;
  }>;
}

export const api = {
  businesses: {
    list: () => fetch(`${API_BASE_URL}/businesses/`),
    create: (request: CreateBusinessRequest) =>
      fetch(`${API_BASE_URL}/businesses/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }),
    get: (id: string) => fetch(`${API_BASE_URL}/businesses/${id}`),
    update: (id: string, business: { name: string }) =>
      fetch(`${API_BASE_URL}/businesses/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(business),
      }),
    delete: (id: string) =>
      fetch(`${API_BASE_URL}/businesses/${id}`, {
        method: "DELETE",
      }),
  },
  employees: {
    list: (businessId?: string) =>
      fetch(
        `${API_BASE_URL}/employees/${
          businessId ? `?business_id=${businessId}` : ""
        }`
      ),
    create: (employee: { email: string; bio?: string; business_id: string }) =>
      fetch(`${API_BASE_URL}/employees/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(employee),
      }),
    get: (id: string) => fetch(`${API_BASE_URL}/employees/${id}`),
    update: (id: string, employee: { email?: string; bio?: string }) =>
      fetch(`${API_BASE_URL}/employees/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(employee),
      }),
    delete: (id: string) =>
      fetch(`${API_BASE_URL}/employees/${id}`, {
        method: "DELETE",
      }),
  },
  questions: {
    list: (businessId?: string) =>
      fetch(
        `${API_BASE_URL}/questions/${
          businessId ? `?business_id=${businessId}` : ""
        }`
      ),
    create: (question: {
      content: string;
      is_follow_up?: boolean;
      business_id: string;
    }) =>
      fetch(`${API_BASE_URL}/questions/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(question),
      }),
    get: (id: string) => fetch(`${API_BASE_URL}/questions/${id}`),
    update: (
      id: string,
      question: { content?: string; is_follow_up?: boolean }
    ) =>
      fetch(`${API_BASE_URL}/questions/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(question),
      }),
    delete: (id: string) =>
      fetch(`${API_BASE_URL}/questions/${id}`, {
        method: "DELETE",
      }),
  },
  interviews: {
    list: (businessId?: string) =>
      fetch(
        `${API_BASE_URL}/interviews/${
          businessId ? `?business_id=${businessId}` : ""
        }`
      ),
    create: (interview: { business_id: string }) =>
      fetch(`${API_BASE_URL}/interviews/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(interview),
      }),
    get: (id: string) => fetch(`${API_BASE_URL}/interviews/${id}`),
    update: (id: string, interview: { business_id?: string }) =>
      fetch(`${API_BASE_URL}/interviews/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(interview),
      }),
    delete: (id: string) =>
      fetch(`${API_BASE_URL}/interviews/${id}`, {
        method: "DELETE",
      }),
    getBusinessDetails: (businessId: string) =>
      fetch(`${API_BASE_URL}/interviews/business/${businessId}/details`),
  },
  simulate: {
    interview: (request: SimulateInterviewRequest) =>
      fetch(`${API_BASE_URL}/simulate/interview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }),
  },
  procedures: {
    startInterview: (request: StartInterviewRequest) =>
      fetch(`${API_BASE_URL}/start-interview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }),
    nextQuestion: (request: { interview_id: string }) =>
      fetch(`${API_BASE_URL}/next-question`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }),
    answerQuestion: (request: {
      interview_id: string;
      question_id: string;
      content: string;
    }) =>
      fetch(`${API_BASE_URL}/answer-question`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }),
  },
};
