import { useIssues } from "@/hooks/use-github";
import { useHashQuery } from "@/hooks/use-hash-query";
import ArticleList from "@/components/ArticleList";
import { Button } from "@/components/ui/button";
import { Loader2, ChevronLeft, ChevronRight } from "lucide-react";
import { useLocation } from "wouter";
import { useEffect } from "react";
import { config } from "@/config";

export default function Home() {
  const [location, setLocation] = useLocation();
  const searchParams = useHashQuery();
  
  const page = parseInt(searchParams.get("page") || "1");
  const label = searchParams.get("label") || undefined;

  // Debug log to verify label detection
  useEffect(() => {
    console.log("Current label filter:", label);
  }, [label]);

  const { issues, loading, error } = useIssues(page, label);

  const handlePrev = () => {
    if (page > 1) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("page", (page - 1).toString());
      const base = location.split("?")[0];
      // We need to manually trigger hash change if wouter doesn't handle query well
      window.location.hash = `${base}?${newParams.toString()}`;
    }
  };

  const handleNext = () => {
    if (issues.length === config.pageSize) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("page", (page + 1).toString());
      const base = location.split("?")[0];
      window.location.hash = `${base}?${newParams.toString()}`;
    }
  };

  const clearFilter = () => {
    setLocation("/");
    // Force hash update to clear query params if setLocation doesn't do it for same path
    if (window.location.hash.includes("?")) {
        window.location.hash = "/";
    }
  };

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [page, label]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh]">
        <p className="text-destructive mb-4">加载失败，请检查网络或 API 配置</p>
        <Button onClick={() => window.location.reload()}>重试</Button>
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-in fade-in duration-500">
      {label && (
        <div className="flex items-center gap-2 text-xl font-bold pb-4 border-b">
          <span>Label:</span>
          <span className="text-primary">{label}</span>
          <Button variant="ghost" size="sm" onClick={clearFilter} className="ml-auto">
            清除筛选
          </Button>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <ArticleList issues={issues} />
      )}

      {!loading && (
        <div className="flex justify-between items-center mt-10">
          <Button
            variant="outline"
            onClick={handlePrev}
            disabled={page <= 1}
          >
            <ChevronLeft className="mr-2 h-4 w-4" /> 上一页
          </Button>
          <span className="text-sm text-muted-foreground">
            第 {page} 页
          </span>
          <Button
            variant="outline"
            onClick={handleNext}
            disabled={issues.length < config.pageSize}
          >
             下一页 <ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
