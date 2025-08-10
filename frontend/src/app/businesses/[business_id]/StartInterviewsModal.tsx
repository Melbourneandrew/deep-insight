"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Brain, User } from "lucide-react";

interface StartInterviewsModalProps {
  isOpen: boolean;
  onClose: () => void;
  businessId: string;
}

export function StartInterviewsModal({
  isOpen,
  onClose,
  businessId,
}: StartInterviewsModalProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleSimulateInterview = async () => {
    setLoading(true);
    try {
      // Navigate to the interviews page to show simulated interviews
      router.push(`/businesses/${businessId}/interview`);
      onClose();
    } catch (error) {
      console.error("Error starting simulated interview:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleTakeInterview = async () => {
    setLoading(true);
    try {
      // Navigate to the interview start page
      router.push(`/businesses/${businessId}/interview/start`);
      onClose();
    } catch (error) {
      console.error("Error starting interview:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Start Interviews</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <p className="text-sm text-gray-600 mb-6">
            Choose how you'd like to proceed with interviews for this business.
          </p>

          <div className="grid grid-cols-2 gap-4">
            <Button
              onClick={handleSimulateInterview}
              disabled={loading}
              className="h-24 flex flex-col items-center justify-center space-y-2 bg-purple-500 hover:bg-purple-600"
            >
              <Brain className="w-6 h-6" />
              <div className="text-center">
                <div className="font-semibold">Simulate Interviews</div>
                <div className="text-xs opacity-90">
                  View AI-generated interview responses
                </div>
              </div>
            </Button>

            <Button
              onClick={handleTakeInterview}
              disabled={loading}
              variant="outline"
              className="h-24 flex flex-col items-center justify-center space-y-2 border-blue-200 hover:bg-blue-50"
            >
              <User className="w-6 h-6" />
              <div className="text-center">
                <div className="font-semibold">Take Interview</div>
                <div className="text-xs opacity-75">
                  Conduct a live interview session
                </div>
              </div>
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
