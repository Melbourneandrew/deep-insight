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
import { type FormEventHandler } from "react";

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

  const handleSubmit: FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    if (!value.trim()) {
      return;
    }
    onSubmit(event);
  };

  return (
    <AIInput onSubmit={handleSubmit}>
      <AIInputTextarea
        onChange={(e) => onChange(e.target.value)}
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
