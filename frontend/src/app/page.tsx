"use client";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
      <div className="text-center max-w-4xl mx-auto px-6">
        <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight">
          Deep Insight
        </h1>
        <h2 className="text-2xl md:text-3xl text-muted-foreground mb-8 font-light">
          DeepWiki for Businesses
        </h2>
        <p className="text-lg md:text-xl text-muted-foreground mb-12 max-w-2xl mx-auto leading-relaxed">
          Transform your business knowledge into actionable insights with our
          intelligent wiki platform
        </p>
        <Button
          size="lg"
          className="text-lg px-8 py-6"
          onClick={() => router.push("/businesses")}
        >
          Get Started
        </Button>
      </div>
    </div>
  );
}
