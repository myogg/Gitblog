import type { GitHubIssue } from "@/types";
import { Link } from "wouter";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

interface ArticleListProps {
  issues: GitHubIssue[];
}

export default function ArticleList({ issues }: ArticleListProps) {
  // Group by year
  const groupedIssues = issues.reduce((acc, issue) => {
    const year = new Date(issue.created_at).getFullYear();
    if (!acc[year]) acc[year] = [];
    acc[year].push(issue);
    return acc;
  }, {} as Record<number, GitHubIssue[]>);

  const years = Object.keys(groupedIssues).sort((a, b) => Number(b) - Number(a));

  if (issues.length === 0) {
    return (
      <div className="text-center py-20 text-muted-foreground">
        暂无文章
      </div>
    );
  }

  return (
    <div className="max-w-[700px] mx-auto">
      {years.map((year) => (
        <div key={year} className="mb-8">
          <h2 className="year-label">{year}年</h2>
          <ul className="article-list">
            {groupedIssues[Number(year)].map((issue) => (
              <li key={issue.id} className="flex items-baseline py-3">
                <span className="article-date">
                  {format(new Date(issue.created_at), "MM-dd")}
                </span>
                <Link href={`/article/${issue.number}`}>
                  <a className="article-title-link">
                    {issue.title}
                  </a>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
