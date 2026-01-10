import { useIssues } from "@/hooks/use-github";
import { useHashQuery } from "@/hooks/use-hash-query";
import ArticleList from "@/components/ArticleList";
import { Button } from "@/components/ui/button";
import { Loader2, ChevronLeft, ChevronRight, AlertTriangle } from "lucide-react";
import { useLocation } from "wouter";
import { useEffect } from "react";
import { config } from "@/config";

export default function Home() {
  const [location, setLocation] = useLocation();
  const searchParams = useHashQuery();
  
  const page = parseInt(searchParams.get("page") || "1");
  const label = searchParams.get("label") || undefined;

  const { issues, loading, error } = useIssues(page, label);

  const handlePrev = () => {
    if (page > 1) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("page", (page - 1).toString());
      const base = location.split("?")[0];
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
    if (window.location.hash.includes("?")) {
        window.location.hash = "/";
    }
  };

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [page, label]);

  if (error) {
    const status = (error as any).response?.status;
    const errorMsg = (error as any).message;
    
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div className="bg-destructive/10 p-4 rounded-full mb-4">
          <AlertTriangle className="h-10 w-10 text-destructive" />
        </div>
        <h2 className="text-xl font-bold mb-2">加载失败</h2>
        
        <div className="bg-muted p-4 rounded-lg text-left text-sm font-mono mb-6 max-w-lg w-full overflow-auto">
          <p className="mb-1"><span className="font-semibold text-foreground">Error:</span> {errorMsg}</p>
          {status && <p className="mb-1"><span className="font-semibold text-foreground">Status Code:</span> {status}</p>}
          <div className="border-t border-border my-2"></div>
          <p className="mb-1 text-muted-foreground">Current Configuration:</p>
          <p>Repo: <span className="text-primary">{config.githubUsername}/{config.githubRepo}</span></p>
        </div>

        <div className="text-sm text-muted-foreground mb-6 max-w-md space-y-2">
          {status === 404 && (
            <p className="text-orange-600 font-medium">
              🔍 <strong>404 错误：</strong> 请检查您的 GitHub 仓库是否为 <strong>Public (公开)</strong>。
              GitHub Issues API 无法访问 Private (私有) 仓库。
            </p>
          )}
          {status === 403 && (
            <p className="text-orange-600 font-medium">
              ⏳ <strong>403 错误：</strong> API 请求频率受限。请稍等几分钟再刷新。
            </p>
          )}
          <p>如果是配置错误，请检查 <code>config.ts</code> 或 GitHub Actions 环境变量。</p>
        </div>

        <Button onClick={() => window.location.reload()}>刷新重试</Button>
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
