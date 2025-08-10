"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Plus, Search, ArrowRight } from "lucide-react";
import CreateBusinessModal from "./CreateBusinessModal";
import { api } from "@/lib/api";

interface Business {
  id: string;
  name: string;
}

export default function BusinessesPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBusinesses = async () => {
    try {
      console.log("Starting fetchBusinesses...");
      setIsLoading(true);
      setError(null);

      console.log(
        "Making API call to:",
        `${
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        }/businesses/`
      );
      const response = await api.businesses.list();
      console.log("server response", response);
      console.log("Response status:", response.status);
      console.log("Response ok:", response.ok);

      if (!response.ok) {
        console.error("Response not ok, status:", response.status);
        throw new Error(
          `Failed to fetch businesses: ${response.status} ${response.statusText}`
        );
      }

      console.log("Parsing JSON...");
      const data = await response.json();
      console.log("Data received:", data);
      setBusinesses(data);
      console.log("Businesses set successfully");
    } catch (err) {
      console.error("Detailed error in fetchBusinesses:", err);
      console.error("Error type:", typeof err);
      console.error("Error name:", err instanceof Error ? err.name : "Unknown");
      console.error(
        "Error message:",
        err instanceof Error ? err.message : String(err)
      );
      setError(
        err instanceof Error ? err.message : "Failed to fetch businesses"
      );
    } finally {
      console.log("fetchBusinesses finally block");
      setIsLoading(false);
    }
  };

  useEffect(() => {
    console.log("fetching businesses");
    fetchBusinesses();
  }, []);

  const filteredBusinesses = businesses.filter((business) =>
    business.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background px-[120px]">
      {/* Header */}
      <div className="max-w-7xl mx-auto px-6 pt-12 pb-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl md:text-3xl font-bold mb-3 tracking-tight">
            Which business would you like to understand?
          </h1>

          {/* Search Bar */}
          <div className="max-w-xl mx-auto mt-6 relative">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <input
                type="text"
                placeholder="Search for businesses (or paste a link)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 text-sm bg-card border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring transition-all"
              />
            </div>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-8">
            <div className="text-muted-foreground">
              <p className="text-base">Loading businesses...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="text-center py-8">
            <div className="text-destructive mb-4">
              <p className="text-base">Error: {error}</p>
              <Button onClick={fetchBusinesses} className="mt-2">
                Try Again
              </Button>
            </div>
          </div>
        )}

        {/* Business Grid */}
        {!isLoading && !error && (
          <div className="flex flex-wrap gap-4">
            {/* Add Business Modal */}
            <div className="w-80">
              <CreateBusinessModal onBusinessCreated={fetchBusinesses} />
            </div>

            {/* Business Cards */}
            {filteredBusinesses.map((business) => (
              <div
                key={business.id}
                className="w-80 group cursor-pointer"
                onClick={() => router.push(`/businesses/${business.id}`)}
              >
                <div className="bg-card border border-border rounded-lg p-4 h-36 flex flex-col transition-all duration-200 hover:border-ring hover:shadow-lg hover:shadow-black/5">
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-lg font-semibold text-card-foreground group-hover:text-primary transition-colors">
                        {business.name}
                      </h3>
                      <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-all duration-200 transform group-hover:translate-x-1" />
                    </div>

                    <p className="text-muted-foreground text-xs mb-3 leading-relaxed">
                      Business profile ready for insights
                    </p>

                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">
                        Click to explore
                      </span>
                      <span className="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs font-medium">
                        Business
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && filteredBusinesses.length === 0 && (
          <div className="text-center py-8">
            <div className="text-muted-foreground mb-4">
              <Search className="w-8 h-8 mx-auto mb-3 opacity-50" />
              {searchQuery ? (
                <>
                  <p className="text-base">
                    No businesses found matching "{searchQuery}"
                  </p>
                  <p className="text-xs">Try adjusting your search terms</p>
                </>
              ) : (
                <>
                  <p className="text-base">No businesses found</p>
                  <p className="text-xs">
                    Get started by creating your first business
                  </p>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
