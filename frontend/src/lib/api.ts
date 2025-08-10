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
};
