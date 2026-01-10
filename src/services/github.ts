import axios from 'axios';
import { config } from '../config';
import type { GitHubIssue, GitHubLabel, GitHubComment, GitHubUser } from '../types';

const API_BASE = `https://api.github.com/repos/${config.githubUsername}/${config.githubRepo}`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    Accept: 'application/vnd.github.v3+json',
  },
});

// Simple in-memory cache
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 60 * 1000; // 1 minute

const getCached = <T>(key: string): T | null => {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  return null;
};

const setCache = (key: string, data: any) => {
  cache.set(key, { data, timestamp: Date.now() });
};

export const githubService = {
  // Get issues (articles)
  getIssues: async (page = 1, per_page = config.pageSize, labels?: string): Promise<GitHubIssue[]> => {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: per_page.toString(),
      state: 'open',
      sort: 'created',
      direction: 'desc',
      creator: config.githubUsername,
    });
    
    // Filter out PRs if possible, though GitHub API mixes them. 
    // We handle PR filtering in the frontend or strictly by creator if needed.
    // creator: config.githubUsername
    
    if (labels) {
      params.append('labels', labels);
    }

    const cacheKey = `issues-${page}-${per_page}-${labels || 'all'}`;
    const cached = getCached<GitHubIssue[]>(cacheKey);
    if (cached) return cached;

    const response = await api.get<GitHubIssue[]>('/issues', { params });
    // Filter out Pull Requests (which are also issues in GitHub API)
    const issues = response.data.filter(issue => !issue.url.includes('/pulls/'));
    
    setCache(cacheKey, issues);
    return issues;
  },

  // Get single issue
  getIssue: async (number: number): Promise<GitHubIssue> => {
    const cacheKey = `issue-${number}`;
    const cached = getCached<GitHubIssue>(cacheKey);
    if (cached) return cached;

    const response = await api.get<GitHubIssue>(`/issues/${number}`);
    setCache(cacheKey, response.data);
    return response.data;
  },

  // Get comments
  getComments: async (number: number): Promise<GitHubComment[]> => {
    const cacheKey = `comments-${number}`;
    const cached = getCached<GitHubComment[]>(cacheKey);
    if (cached) return cached;

    const response = await api.get<GitHubComment[]>(`/issues/${number}/comments`);
    setCache(cacheKey, response.data);
    return response.data;
  },

  // Get all labels
  getLabels: async (): Promise<GitHubLabel[]> => {
    const cacheKey = 'labels';
    const cached = getCached<GitHubLabel[]>(cacheKey);
    if (cached) return cached;

    const response = await api.get<GitHubLabel[]>('/labels');
    setCache(cacheKey, response.data);
    return response.data;
  },

  // Search issues
  searchIssues: async (query: string): Promise<{ items: GitHubIssue[], total_count: number }> => {
    // Search API is different base
    // https://api.github.com/search/issues?q=repo:OWNER/NAME+QUERY
    const q = `repo:${config.githubUsername}/${config.githubRepo} type:issue state:open ${query}`;
    const response = await axios.get('https://api.github.com/search/issues', {
      params: { q },
      headers: { Accept: 'application/vnd.github.v3+json' }
    });
    return response.data;
  },
  
  // Get User Info
  getUser: async (): Promise<GitHubUser> => {
    const cacheKey = `user-${config.githubUsername}`;
    const cached = getCached<GitHubUser>(cacheKey);
    if (cached) return cached;
    
    const response = await axios.get(`https://api.github.com/users/${config.githubUsername}`);
    setCache(cacheKey, response.data);
    return response.data;
  }
};
