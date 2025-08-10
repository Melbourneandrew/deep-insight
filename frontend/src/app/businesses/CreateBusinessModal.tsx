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
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus } from "lucide-react";
import { api, CreateBusinessRequest } from "@/lib/api";

interface CreateBusinessModalProps {
  onBusinessCreated: () => void;
}

const businessNames = [
  "Wobble",
  "Fizzbuzz",
  "Snuggles",
  "Giggles",
  "Bumble",
  "Pickle",
  "Waffle",
  "Noodle",
  "Sprinkle",
  "Bubble",
  "Cuddle",
  "Doodle",
  "Wiggle",
  "Tickle",
  "Squish",
  "Fluff",
  "Bounce",
  "Sparkle",
  "Jelly",
  "Muffin",
  "Puddle",
  "Twinkle",
  "Zippy",
  "Fuzzy",
  "Jolly",
  "Silly",
  "Quirky",
  "Peppy",
];

const businessDesignations = [
  "& Associates",
  "Incorporated",
  "LLC",
  "Enterprises",
  "Industries",
  "Solutions",
  "Technologies",
  "Dynamics",
  "Systems",
  "Ventures",
  "Holdings",
  "Group",
  "Corporation",
  "Company",
  "Partners",
  "International",
  "Global",
  "Unlimited",
  "Express",
  "Premium",
];

const generateRandomBusinessName = () => {
  const randomName =
    businessNames[Math.floor(Math.random() * businessNames.length)];
  const randomDesignation =
    businessDesignations[
      Math.floor(Math.random() * businessDesignations.length)
    ];
  return `${randomName} ${randomDesignation}`;
};

export default function CreateBusinessModal({
  onBusinessCreated,
}: CreateBusinessModalProps) {
  const [open, setOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: generateRandomBusinessName(),
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.businesses.create({
        name: formData.name.trim(),
        // seed_data is optional - if not provided, backend will use default seed data
      });

      if (!response.ok) {
        throw new Error("Failed to create business");
      }

      // Reset form and close modal
      setFormData({ name: "" });
      setOpen(false);
      onBusinessCreated();
    } catch (error) {
      console.error("Error creating business:", error);
      // You could add a toast notification here
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <div className="group cursor-pointer">
          <div className="bg-gradient-to-br from-primary/5 to-primary/10 border border-dashed border-primary/30 rounded-lg p-6 h-36 flex flex-col items-center justify-center text-center transition-all duration-200 hover:border-primary/50 hover:bg-primary/5 hover:shadow-md">
            <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center mb-3 group-hover:bg-primary/20 transition-colors">
              <Plus className="w-4 h-4 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-1 text-foreground">
              Add Business
            </h3>
            <p className="text-muted-foreground text-xs">
              Create a new business profile to start gathering insights
            </p>
          </div>
        </div>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New Business</DialogTitle>
          <DialogDescription>
            Add a new business to start gathering insights and conducting
            interviews.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">
                Name
              </Label>
              <Input
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Enter business name"
                className="col-span-3"
                required
                disabled={isLoading}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !formData.name.trim()}>
              {isLoading ? "Creating..." : "Create Business"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
