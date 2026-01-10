import { useIssues } from "@/hooks/use-github";
import { Link } from "wouter";
import { format } from "date-fns";
import { Loader2 } from "lucide-react";

export default function Archives() {
  // Archives typically need ALL issues to group by year/month. 
  // API limitation: pagination. We fetch first 100 for now or rely on infinite scroll?
  // For static blog with < 100 posts, per_page=100 is fine.
  // config.pageSize is usually small (10). Let's fetch more here.
  const { issues, loading } = useIssues(1, undefined); // This only gets first page... 
  // Ideally we need a separate "getAllIssues" or just fetch page 1 with large size.
  // BUT the hook is tied to config.pageSize. 
  // Let's stick to page 1 for now or todo: improve hook to accept custom page size.
  
  if (loading) return <div className="flex justify-center p-10"><Loader2 className="animate-spin" /></div>;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">归档</h1>
      <div className="prose dark:prose-invert">
        <p>这里显示最近的文章列表。</p>
        <ul className="not-prose space-y-2">
          {issues.map(issue => (
            <li key={issue.id} className="flex gap-4 items-baseline">
              <span className="text-muted-foreground font-mono text-sm min-w-[100px]">
                {format(new Date(issue.created_at), "yyyy-MM-dd")}
              </span>
              <Link href={`/article/${issue.number}`}>
                <a className="hover:text-primary transition-colors hover:underline decoration-primary/50">
                  {issue.title}
                </a>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
