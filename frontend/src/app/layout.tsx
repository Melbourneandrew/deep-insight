import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import DeepInsightLogo from "./DeepInsightLogo";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Deep Insight - DeepWiki for Businesses",
  description:
    "Transform your business knowledge into actionable insights with our intelligent wiki platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/deepinsight_logo.svg" type="image/svg+xml" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <nav className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex items-center justify-between h-16">
              {/* Logo and Brand */}
              <Link
                href="/"
                className="flex items-center space-x-2 hover:opacity-80 transition-opacity"
              >
                <DeepInsightLogo size={24} />
                <span className="text-lg font-semibold">Deep Insight</span>
              </Link>

              {/* Navigation Items */}
              <div className="flex items-center space-x-6">
                <Link
                  href="/businesses"
                  className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
                >
                  Businesses
                </Link>
                <Link
                  href="/about"
                  className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
                >
                  About
                </Link>
                <Button size="sm" variant="default">
                  <Share2 className="h-4 w-4 mr-2" />
                  Share
                </Button>
              </div>
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
