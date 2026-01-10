import { useLabels } from "@/hooks/use-github";
import { Link } from "wouter";
import { Badge } from "@/components/ui/badge";
import { Loader2, Tag } from "lucide-react";

export default function Tags() {
  const { labels, loading } = useLabels();

  if (loading) return <div className="flex justify-center p-10"><Loader2 className="animate-spin" /></div>;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">标签</h1>
      <div className="flex flex-wrap gap-4">
        {labels.map(label => (
          <Link key={label.id} href={`/?label=${label.name}`}>
            <a>
              <Badge className="text-lg py-2 px-4 hover:scale-105 transition-transform cursor-pointer">
                <Tag className="mr-2 h-4 w-4" />
                {label.name}
              </Badge>
            </a>
          </Link>
        ))}
      </div>
    </div>
  );
}
