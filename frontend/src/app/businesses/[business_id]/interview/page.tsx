"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, User, MessageSquare, Boxes } from "lucide-react";
import { api } from "@/lib/api";
import BuildWikiLoadingModal from "./BuildWikiLoadingModal";

interface QuestionResponseDetail {
  question_id: string;
  question_content: string;
  question_is_follow_up: boolean;
  employee_id: string;
  employee_email: string;
  response_content: string;
}

interface InterviewDetail {
  interview_id: string;
  business_id: string;
  questions_and_responses: QuestionResponseDetail[];
}

interface Business {
  id: string;
  name: string;
}

export default function InterviewsPage() {
  const params = useParams();
  const router = useRouter();
  const businessId = params.business_id as string;

  const [business, setBusiness] = useState<Business | null>(null);
  const [interviews, setInterviews] = useState<InterviewDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [buildingWiki, setBuildingWiki] = useState(false);

  // Load data function
  const loadData = async (isInitialLoad = false) => {
    try {
      if (isInitialLoad) {
        setLoading(true);
      }
      const [businessResponse, interviewsResponse] = await Promise.all([
        api.businesses.get(businessId),
        api.interviews.getBusinessDetails(businessId),
      ]);

      if (!businessResponse.ok) {
        throw new Error("Failed to load business");
      }
      if (!interviewsResponse.ok) {
        throw new Error("Failed to load interviews");
      }

      const businessData = await businessResponse.json();
      const interviewsData = await interviewsResponse.json();

      setBusiness(businessData);
      setInterviews(interviewsData);
      setError(null); // Clear any previous errors
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  };

  // Initial load
  useEffect(() => {
    if (businessId) {
      loadData(true);
    }
  }, [businessId]);

  // Polling for updates every second
  useEffect(() => {
    if (!businessId) return;

    const interval = setInterval(() => {
      loadData(false);
    }, 1000);

    return () => clearInterval(interval);
  }, [businessId]);

  const handleBuildWiki = async () => {
    try {
      setBuildingWiki(true);
      const response = await api.procedures.buildWiki({
        business_id: businessId,
      });

      if (!response.ok) {
        throw new Error("Failed to build wiki");
      }

      // You might want to show a success message or redirect here
      console.log("Wiki build started successfully");

      // Keep the modal open for a minimum duration to show the process
      setTimeout(() => {
        setBuildingWiki(false);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to build wiki");
      setBuildingWiki(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-gray-600">Loading interviews...</div>
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

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            onClick={() => router.push(`/businesses/${businessId}`)}
            className="p-2"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
              INTERVIEWS
            </div>
            <h1 className="text-3xl font-bold text-gray-900">
              {business?.name} - Interview Results
            </h1>
          </div>
        </div>
        <Button
          onClick={handleBuildWiki}
          disabled={buildingWiki || interviews.length === 0}
          className="flex items-center space-x-2 font-bold"
        >
          <Boxes className="w-5 h-5" />
          <span>{buildingWiki ? "Building Wiki..." : "Build Wiki"}</span>
        </Button>
      </div>

      {/* Content */}
      {interviews.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No interviews found
          </h3>
          <p className="text-gray-600 mb-4">
            There are no completed interviews for this business yet.
          </p>
          <Button
            onClick={() => router.push(`/businesses/${businessId}`)}
            variant="outline"
          >
            Go Back to Business
          </Button>
        </div>
      ) : (
        <div className="space-y-8">
          {interviews.map((interview) => (
            <div
              key={interview.interview_id}
              className="bg-white rounded-lg border border-gray-200 shadow-sm"
            >
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">
                  Interview #{interview.interview_id.slice(0, 8)}
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  {interview.questions_and_responses.length} questions answered
                </p>
              </div>

              <div className="p-6">
                {interview.questions_and_responses.length === 0 ? (
                  <p className="text-gray-500 italic">
                    No responses recorded for this interview.
                  </p>
                ) : (
                  <div className="space-y-6">
                    {interview.questions_and_responses.map((qr, index) => (
                      <div
                        key={`${qr.question_id}-${qr.employee_id}`}
                        className={`border-l-4 pl-4 ${
                          qr.question_is_follow_up
                            ? "border-orange-300"
                            : "border-blue-200"
                        }`}
                      >
                        <div className="flex items-start space-x-3 mb-3">
                          <div
                            className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                              qr.question_is_follow_up
                                ? "bg-orange-100"
                                : "bg-blue-100"
                            }`}
                          >
                            <span
                              className={`text-sm font-semibold ${
                                qr.question_is_follow_up
                                  ? "text-orange-600"
                                  : "text-blue-600"
                              }`}
                            >
                              {index + 1}
                            </span>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <h3 className="font-semibold text-gray-900">
                                {qr.question_content}
                              </h3>
                              {qr.question_is_follow_up ? (
                                <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">
                                  Follow-up
                                </span>
                              ) : (
                                <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                                  Scripted
                                </span>
                              )}
                            </div>
                            <div className="flex items-center space-x-2 text-sm text-gray-600 mb-3">
                              <User className="w-4 h-4" />
                              <span>Answered by: {qr.employee_email}</span>
                            </div>
                            <div className="bg-gray-50 rounded-lg p-4">
                              <p className="text-gray-800 leading-relaxed">
                                {qr.response_content}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Build Wiki Loading Modal */}
      <BuildWikiLoadingModal
        isOpen={buildingWiki}
        headerText="Building Wiki"
        duration={25}
      />
    </div>
  );
}
