import { Link } from "wouter";
import { format } from "date-fns";
import type { GitHubIssue } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CalendarIcon } from "lucide-react";

interface ArticleCardProps {
  issue: GitHubIssue;
}

// Helper to strip markdown and html for summary
function getSummary(body: string): string {
  if (!body) return "";

  // 1. Try to find manual split <!-- more -->
  const moreIndex = body.indexOf("<!-- more -->");
  let content = moreIndex !== -1 ? body.slice(0, moreIndex) : body;

  // 2. Strip Markdown & HTML
  content = content
    // Remove HTML tags (including video/audio)
    .replace(/<[^>]*>/g, "")
    // Remove images ![]()
    .replace(/!\[.*?\]\(.*?\)/g, "[图片]")
    // Remove links []() -> keep text
    .replace(/\[(.*?)\]\(.*?\)/g, "$1")
    // Remove headers, bold, italic, code
    .replace(/[#*`>~]/g, "")
    // Remove continuous whitespace
    .replace(/\s+/g, " ")
    .trim();

  // 3. Truncate if no manual split was found (or if split part is still too long)
  // If manual split exists, we respect it (unless it's excessively long, but usually users know what they do)
  if (moreIndex === -1 && content.length > 150) {
    return content.slice(0, 150) + "...";
  }

  return content;
}

export default function ArticleCard({ issue }: ArticleCardProps) {
  const summary = getSummary(issue.body);

  return (
    <Card className="mb-4 hover:shadow-md transition-shadow duration-200 border-l-4 border-l-primary/0 hover:border-l-primary">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <Link href={`/article/${issue.number}`}>
            <a className="group">
              <CardTitle className="text-xl font-bold group-hover:text-primary transition-colors">
                {issue.title}
              </CardTitle>
            </a>
          </Link>
          <div className="flex items-center text-sm text-muted-foreground whitespace-nowrap ml-4">
            <CalendarIcon className="mr-1 h-3 w-3" />
            {format(new Date(issue.created_at), "MMM d")}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {summary && (
          <p className="text-muted-foreground text-sm line-clamp-3 mb-3 leading-relaxed">
            {summary}
          </p>
        )}
        <div className="flex flex-wrap gap-2">
          {issue.labels.map((label) => (
            <Link key={label.id} href={`/?label=${label.name}`}>
              <a>
                <Badge 
                  variant="secondary" 
                  className="hover:bg-primary hover:text-primary-foreground transition-colors"
                >
                  {label.name}
                </Badge>
              </a>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
