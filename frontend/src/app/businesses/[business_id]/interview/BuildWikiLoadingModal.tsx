"use client";

import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";

// Define predefined step sets for wiki building
const PROGRESS_MESSAGE_SETS = {
  "wiki-building": [
    "Analyzing interview responses",
    "Extracting key insights",
    "Organizing knowledge structure",
    "Creating documentation sections",
    "Generating content summaries",
    "Building cross-references",
    "Formatting documentation",
    "Validating completeness",
    "Finalizing wiki structure",
  ],
} as const;

type StepSetKey = keyof typeof PROGRESS_MESSAGE_SETS;

interface BuildWikiLoadingModalProps {
  isOpen: boolean;
  headerText?: string;
  duration?: number; // Duration in seconds, defaults to 30
  progressMessageSet?: StepSetKey; // Predefined step set to use
  customProgressMessageSet?: string[]; // Custom steps array (overrides stepSet)
}

export default function BuildWikiLoadingModal({
  isOpen,
  headerText = "Building Wiki",
  duration = 30,
  progressMessageSet = "wiki-building",
  customProgressMessageSet,
}: BuildWikiLoadingModalProps) {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  // Use custom steps if provided, otherwise use the selected step set
  const steps =
    customProgressMessageSet || PROGRESS_MESSAGE_SETS[progressMessageSet];

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setProgress(0);
      setCurrentStep(0);
      setIsComplete(false);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const totalTime = duration * 1000; // Convert to milliseconds
    const intervalTime = 100; // Update every 100ms
    const increment = (100 / totalTime) * intervalTime;

    const interval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + increment;
        if (newProgress >= 100) {
          clearInterval(interval);
          setIsComplete(true);
          return 100;
        }
        return newProgress;
      });
    }, intervalTime);

    return () => clearInterval(interval);
  }, [duration, isOpen]);

  useEffect(() => {
    if (isComplete || !isOpen) return;

    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % steps.length);
    }, 2500);

    return () => clearInterval(stepInterval);
  }, [steps.length, isComplete, isOpen]);

  // Create grid of blocks for the loading animation
  const createBlocks = () => {
    const blocks = [];
    const totalBlocks = 48;

    for (let i = 0; i < totalBlocks; i++) {
      const isActive = (i / totalBlocks) * 100 <= progress;
      const delay = (i * 50) % 1000;

      blocks.push(
        <div
          key={i}
          className={`w-3 h-3 transition-all duration-300 ease-in-out rounded-sm ${
            isActive
              ? "bg-primary shadow-sm animate-pulse"
              : "bg-gray-200 border border-gray-300"
          }`}
          style={{
            animationDelay: `${delay}ms`,
          }}
        />
      );
    }
    return blocks;
  };

  return (
    <Dialog open={isOpen}>
      <DialogContent className="max-w-2xl" showCloseButton={false}>
        <div className="flex flex-col items-center space-y-8 p-4">
          {/* Main Title */}
          <DialogTitle className="sr-only">{headerText}</DialogTitle>
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-light tracking-wider text-gray-800 uppercase">
              {headerText}
            </h1>
            <div className="w-16 h-px bg-gray-400 mx-auto" />
          </div>

          {/* Block Grid Animation */}
          <div className="relative">
            <div className="grid grid-cols-12 gap-1 p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
              {createBlocks()}
            </div>

            {/* Progress indicator overlay */}
            <div className="absolute -bottom-2 left-0 right-0 flex justify-center">
              <div className="bg-white px-3 py-1 rounded-full border border-gray-200 text-xs font-mono text-gray-600 shadow-sm">
                {Math.round(progress)}%
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full max-w-md space-y-3">
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-300 ease-out rounded-full"
                style={{
                  width: `${progress}%`,
                }}
              />
            </div>

            {/* Current Step */}
            <div className="text-center min-h-[3rem] flex items-center justify-center">
              <p className="text-sm font-mono text-gray-600 transition-opacity duration-500">
                {isComplete
                  ? "Wiki building is taking longer than expected. The process is still running in the background. Please hang tight!"
                  : steps[currentStep]}
              </p>
            </div>
          </div>

          {/* Additional info */}
          <div className="text-center text-xs text-gray-500 max-w-md">
            <p>
              We're processing your interview data and creating comprehensive
              documentation. This process may take a few moments depending on
              the amount of content.
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
