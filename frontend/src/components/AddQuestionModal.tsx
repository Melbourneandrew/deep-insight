"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface AddQuestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (question: {
    content: string;
    is_follow_up?: boolean;
  }) => Promise<void>;
}

export function AddQuestionModal({
  isOpen,
  onClose,
  onAdd,
}: AddQuestionModalProps) {
  const [content, setContent] = useState("");
  const [isFollowUp, setIsFollowUp] = useState(false);
  const [isAdding, setIsAdding] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setIsAdding(true);
    try {
      await onAdd({
        content: content.trim(),
        is_follow_up: isFollowUp,
      });
      setContent("");
      setIsFollowUp(false);
      onClose();
    } catch (error) {
      console.error("Failed to add question:", error);
    } finally {
      setIsAdding(false);
    }
  };

  const handleClose = () => {
    setContent("");
    setIsFollowUp(false);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create Question</DialogTitle>
          <DialogDescription>
            Add a new question to this business.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="content">Question *</Label>
              <Input
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="What is your question?"
                required
              />
            </div>
            <div className="flex items-center space-x-2">
              <input
                id="is_follow_up"
                type="checkbox"
                checked={isFollowUp}
                onChange={(e) => setIsFollowUp(e.target.checked)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <Label htmlFor="is_follow_up">Follow-up question</Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isAdding}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isAdding || !content.trim()}>
              {isAdding ? "Creating..." : "Create Question"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
