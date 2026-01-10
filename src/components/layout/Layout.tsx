import type { ReactNode } from "react";
import Header from "./Header";
import Footer from "./Footer";
import { ScrollArea } from "@/components/ui/scroll-area";

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-background font-sans antialiased">
      <Header />
      <main className="flex-1 w-full max-w-[700px] mx-auto px-6 sm:px-8 py-8">
        {children}
      </main>
      <Footer />
    </div>
  );
}
