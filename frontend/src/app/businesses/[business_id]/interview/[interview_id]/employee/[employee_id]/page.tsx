"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, NextQuestionResponse, AnswerQuestionResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import DeepInsightLogo from "@/app/DeepInsightLogo";
import PromptInput from "./PromptInput";

export default function InterviewQuestionPage() {
  const params = useParams();
  const router = useRouter();
  const interviewId = params.interview_id as string;

  const [currentQuestion, setCurrentQuestion] =
    useState<NextQuestionResponse | null>(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch the next question when component mounts
  useEffect(() => {
    fetchNextQuestion();
  }, [interviewId]);

  const fetchNextQuestion = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.procedures.nextQuestion({
        interview_id: interviewId,
      });

      if (!response.ok) {
        throw new Error(
          `Failed to fetch next question: ${response.statusText}`
        );
      }

      const data: NextQuestionResponse = await response.json();
      setCurrentQuestion(data);

      // If interview is over, redirect or show completion message
      if (data.is_interview_over) {
        // You might want to redirect to a completion page or show a message
        console.log("Interview completed!");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!answer.trim() || !currentQuestion?.question) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await api.procedures.answerQuestion({
        interview_id: interviewId,
        question_id: currentQuestion.question.id,
        content: answer.trim(),
      });

      if (!response.ok) {
        throw new Error(`Failed to submit answer: ${response.statusText}`);
      }

      const data: AnswerQuestionResponse = await response.json();

      if (data.success) {
        // Clear the answer input
        setAnswer("");
        // Fetch the next question
        await fetchNextQuestion();
      } else {
        throw new Error("Failed to submit answer");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white">
        <div className="text-center flex flex-col items-center">
          <div className="relative flex items-center justify-center w-16 h-16 mb-4">
            <div className="absolute inset-0 rounded-full border-2 border-blue-200 border-t-blue-500 animate-spin"></div>
            <DeepInsightLogo size={24} className="text-blue-600" />
          </div>
          <p className="text-gray-600">Loading next question...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">Error</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={fetchNextQuestion}>Try Again</Button>
        </div>
      </div>
    );
  }

  if (currentQuestion?.is_interview_over) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-2xl font-bold text-green-600 mb-4">
            🎉 Interview Complete!
          </div>
          <p className="text-gray-600 mb-6">
            Thank you for completing the interview. All questions have been
            answered.
          </p>
          <Button onClick={() => router.push("/businesses")}>
            Return to Businesses
          </Button>
        </div>
      </div>
    );
  }

  if (!currentQuestion?.question) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">No question available</p>
          <Button onClick={fetchNextQuestion} className="mt-4">
            Refresh
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center p-4 mt-[150px]">
      <div className="w-full max-w-2xl">
        <div className="p-8">
          {/* Question */}
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {currentQuestion.question.content}
            </h1>
            {currentQuestion.question.is_follow_up && (
              <span className="inline-block bg-blue-100 text-blue-800 text-sm font-medium px-2.5 py-0.5 rounded">
                Follow-up Question
              </span>
            )}
          </div>

          {/* Answer Form */}
          <div className="space-y-6">
            <PromptInput
              value={answer}
              onChange={setAnswer}
              onSubmit={handleSubmitAnswer}
              disabled={isSubmitting}
              placeholder="Type your answer here..."
              isSubmitting={isSubmitting}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
