"use client";
import {
  AIInput,
  AIInputButton,
  AIInputSubmit,
  AIInputTextarea,
  AIInputToolbar,
  AIInputTools,
} from "@/components/ui/shadcn-io/ai/input";
import { MicIcon, PlusIcon } from "lucide-react";
import { type FormEventHandler, useCallback } from "react";

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  disabled?: boolean;
  placeholder?: string;
  isSubmitting?: boolean;
}

export default function PromptInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder = "Type your answer here...",
  isSubmitting = false,
}: PromptInputProps) {
  const status = isSubmitting ? "streaming" : "ready";

  // Auto-focus using callback ref
  const textareaCallbackRef = useCallback(
    (element: HTMLTextAreaElement | null) => {
      if (element && !disabled) {
        // Small delay to ensure the element is fully mounted
        setTimeout(() => {
          element.focus();
        }, 0);
      }
    },
    [disabled]
  );

  const handleSubmit: FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    if (!value.trim()) {
      return;
    }
    onSubmit(event);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (value.trim() && !disabled) {
        // Create a synthetic form event
        const syntheticEvent = new Event("submit", {
          bubbles: true,
          cancelable: true,
        }) as any;
        syntheticEvent.preventDefault = () => {};
        onSubmit(syntheticEvent);
      }
    }
  };

  return (
    <AIInput onSubmit={handleSubmit}>
      <AIInputTextarea
        ref={textareaCallbackRef}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
      />
      <AIInputToolbar>
        <AIInputTools>
          <AIInputButton disabled={disabled}>
            <PlusIcon size={16} />
          </AIInputButton>
          <AIInputButton disabled={disabled}>
            <MicIcon size={16} />
          </AIInputButton>
        </AIInputTools>
        <AIInputSubmit disabled={!value.trim() || disabled} status={status} />
      </AIInputToolbar>
    </AIInput>
  );
}
