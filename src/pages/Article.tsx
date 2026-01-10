import { useIssue } from "@/hooks/use-github";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import WalineComment from "@/components/WalineComment";
import { useRoute } from "wouter";
import { format } from "date-fns";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CalendarIcon, User, Tag } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Link } from "wouter";

export default function Article() {
  const [match, params] = useRoute("/article/:id");
  const id = match && params?.id ? parseInt(params.id) : 0;
  
  const { issue, loading, error } = useIssue(id);

  if (loading) {
    return (
      <div className="space-y-4 max-w-3xl mx-auto">
        <Skeleton className="h-12 w-3/4" />
        <div className="flex gap-4">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-20" />
        </div>
        <Skeleton className="h-[400px] w-full mt-8" />
      </div>
    );
  }

  if (error || !issue) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold mb-4">文章未找到</h2>
        <p className="text-muted-foreground mb-8">该文章可能已被删除或 ID 错误</p>
        <Link href="/">
          <a className="text-primary hover:underline">返回首页</a>
        </Link>
      </div>
    );
  }

  return (
    <article className="max-w-4xl mx-auto animate-in slide-in-from-bottom-4 duration-500">
      <header className="mb-8 text-center md:text-left">
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-4 justify-center md:justify-start">
          <div className="flex items-center">
            <CalendarIcon className="mr-1 h-4 w-4" />
            {format(new Date(issue.created_at), "MMMM d, yyyy")}
          </div>
          <div className="flex items-center">
            <User className="mr-1 h-4 w-4" />
            {issue.user.login}
          </div>
        </div>

        <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight lg:text-5xl mb-6 text-balance">
          {issue.title}
        </h1>

        <div className="flex flex-wrap gap-2 justify-center md:justify-start">
          {issue.labels.map((label) => (
            <Link key={label.id} href={`/?label=${label.name}`}>
              <a>
                <Badge variant="outline" className="cursor-pointer hover:bg-secondary">
                  <Tag className="mr-1 h-3 w-3" />
                  {label.name}
                </Badge>
              </a>
            </Link>
          ))}
        </div>
      </header>
      
      <Separator className="my-8" />

      <div className="min-h-[300px]">
        <MarkdownRenderer content={issue.body} />
      </div>

      <WalineComment path={`/articles/article-${id}.html`} />
    </article>
  );
}
