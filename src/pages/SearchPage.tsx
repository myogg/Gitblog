import { useSearch } from "@/hooks/use-github";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import ArticleCard from "@/components/ArticleCard";
import { Loader2, Search } from "lucide-react";
import emptyImg from "@/assets/empty.png";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const { results, loading } = useSearch(query);

  return (
    <div className="space-y-8 min-h-[60vh]">
      <h1 className="text-3xl font-bold">搜索</h1>
      <div className="relative">
        <Search className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
        <Input 
          className="pl-10 h-12 text-lg" 
          placeholder="搜索文章标题或内容..." 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
      </div>

      {loading && (
        <div className="flex justify-center py-10">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {!loading && query && results.length === 0 && (
        <div className="flex flex-col items-center py-10 opacity-80">
          <img src={emptyImg} alt="No results" className="w-64 mb-4" />
          <p className="text-muted-foreground">未找到相关文章</p>
        </div>
      )}

      <div className="space-y-4">
        {results.map(issue => (
          <ArticleCard key={issue.id} issue={issue} />
        ))}
      </div>
    </div>
  );
}
