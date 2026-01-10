import { useComments } from "@/hooks/use-github";
import { format } from "date-fns";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import MarkdownRenderer from "./MarkdownRenderer";
import { Card } from "@/components/ui/card";
import { config } from "@/config";
import { Button } from "@/components/ui/button";

interface CommentSectionProps {
  issueNumber: number;
}

export default function CommentSection({ issueNumber }: CommentSectionProps) {
  const { comments, loading } = useComments(issueNumber);

  if (loading) {
    return <Skeleton className="h-40 w-full" />;
  }

  return (
    <div className="mt-12 pt-8 border-t">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-2xl font-bold">评论 ({comments.length})</h3>
        <a 
          href={`https://github.com/${config.githubUsername}/${config.githubRepo}/issues/${issueNumber}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          <Button variant="outline" size="sm">
            前往 GitHub 评论
          </Button>
        </a>
      </div>

      {comments.length === 0 ? (
        <div className="text-center py-10 text-muted-foreground bg-muted/20 rounded-lg">
          暂无评论，点击上方按钮去 GitHub 抢沙发
        </div>
      ) : (
        <div className="space-y-6">
          {comments.map((comment) => (
            <Card key={comment.id} className="p-6 bg-transparent border-none shadow-none ring-1 ring-border/50">
              <div className="flex gap-4">
                <Avatar className="h-10 w-10 border">
                  <AvatarImage src={comment.user.avatar_url} />
                  <AvatarFallback>{comment.user.login[0].toUpperCase()}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-sm">
                      {comment.user.login}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {format(new Date(comment.created_at), "yyyy-MM-dd HH:mm")}
                    </span>
                  </div>
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <MarkdownRenderer content={comment.body} />
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
