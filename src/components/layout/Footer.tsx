import { config } from "@/config";

export default function Footer() {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="border-t py-8 mt-auto bg-muted/30">
      <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
        <p>
          © {currentYear} {config.title}. Designed and developed by {config.author}.
        </p>
        <p className="mt-2 text-xs">
          Powered by React, Vite & GitHub Issues
        </p>
      </div>
    </footer>
  );
}
