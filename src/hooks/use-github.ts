import { useState, useEffect, useCallback } from 'react';
import { githubService } from '../services/github';
import type { GitHubIssue, GitHubLabel, GitHubComment, GitHubUser } from '../types';
import { toast } from 'sonner';

export function useIssues(page = 1, labels?: string) {
  const [issues, setIssues] = useState<GitHubIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    
    githubService.getIssues(page, undefined, labels)
      .then(data => {
        if (mounted) {
          setIssues(data);
          setError(null);
        }
      })
      .catch(err => {
        if (mounted) {
          setError(err);
          console.error("Failed to fetch issues:", err);
          // Only show toast for actual errors, not just empty states
          if (err.response?.status === 403) {
            toast.error("GitHub API 访问受限，请稍后再试");
          }
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [page, labels]);

  return { issues, loading, error };
}

export function useIssue(number: number) {
  const [issue, setIssue] = useState<GitHubIssue | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!number || isNaN(number)) return;
    
    let mounted = true;
    setLoading(true);
    
    githubService.getIssue(number)
      .then(data => {
        if (mounted) {
          setIssue(data);
          setError(null);
        }
      })
      .catch(err => {
        if (mounted) {
          setError(err);
          console.error(`Failed to fetch issue ${number}:`, err);
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => { mounted = false; };
  }, [number]);

  return { issue, loading, error };
}

export function useComments(number: number) {
  const [comments, setComments] = useState<GitHubComment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!number || isNaN(number)) return;

    githubService.getComments(number)
      .then(setComments)
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [number]);

  return { comments, loading };
}

export function useLabels() {
  const [labels, setLabels] = useState<GitHubLabel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    githubService.getLabels()
      .then(setLabels)
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return { labels, loading };
}

export function useSearch(query: string) {
  const [results, setResults] = useState<GitHubIssue[]>([]);
  const [loading, setLoading] = useState(false);

  // Debounce could be handled in UI, but this is a simple trigger
  const search = useCallback(async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      const data = await githubService.searchIssues(q);
      setResults(data.items);
    } catch (err) {
      console.error(err);
      toast.error("搜索失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (query) search(query);
    }, 500);
    return () => clearTimeout(timer);
  }, [query, search]);

  return { results, loading };
}

export function useUser() {
  const [user, setUser] = useState<GitHubUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    githubService.getUser()
      .then(setUser)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return { user, loading };
}
