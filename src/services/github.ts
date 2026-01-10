import axios from 'axios';
import { config } from '../config';
import { GitHubIssue, GitHubLabel, GitHubComment, GitHubUser } from '../types';

const API_BASE = `https://api.github.com/repos/${config.githubUsername}/${config.githubRepo}`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    Accept: 'application/vnd.github.v3+json',
  },
});

// LocalStorage Cache Configuration
const CACHE_PREFIX = 'gitblog-cache-';
const CACHE_TTL = 15 * 60 * 1000; // 15 minutes (extended to prevent 403)

interface CacheItem<T> {
  data: T;
  timestamp: number;
}

const getCached = <T>(key: string): T | null => {
  try {
    const itemStr = localStorage.getItem(CACHE_PREFIX + key);
    if (!itemStr) return null;

    const item: CacheItem<T> = JSON.parse(itemStr);
    const now = Date.now();

    // Check if expired
    if (now - item.timestamp > CACHE_TTL) {
      localStorage.removeItem(CACHE_PREFIX + key);
      return null;
    }

    return item.data;
  } catch (e) {
    console.error('Cache retrieval failed', e);
    return null;
  }
};

const setCache = (key: string, data: any) => {
  try {
    const item: CacheItem<any> = {
      data,
      timestamp: Date.now(),
    };
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(item));
  } catch (e) {
    console.warn('Cache storage failed (quota exceeded?)', e);
    // If quota exceeded, we might want to clear old cache, but for now just ignoring is safe
  }
};

export const githubService = {
  // Get issues (articles)
  getIssues: async (page = 1, per_page = config.pageSize, labels?: string): Promise<GitHubIssue[]> => {
    // Generate a unique cache key based on params
    const cacheKey = `issues-${config.githubUsername}-${config.githubRepo}-${page}-${per_page}-${labels || 'all'}`;
    
    // Try cache first
    const cached = getCached<GitHubIssue[]>(cacheKey);
    if (cached) {
      console.log(`[Cache Hit] Issues: ${cacheKey}`);
      return cached;
    }

    const params = new URLSearchParams({
      page: page.toString(),
      per_page: per_page.toString(),
      state: 'open',
      sort: 'created',
      direction: 'desc',
      creator: config.githubUsername,
    });
    
    if (labels) {
      params.append('labels', labels);
    }

    const response = await api.get<GitHubIssue[]>('/issues', { params });
    // Filter out Pull Requests
    const issues = response.data.filter(issue => !issue.url.includes('/pulls/'));
    
    setCache(cacheKey, issues);
    return issues;
  },

  // Get single issue
  getIssue: async (number: number): Promise<GitHubIssue> => {
    const cacheKey = `issue-${config.githubUsername}-${config.githubRepo}-${number}`;
    const cached = getCached<GitHubIssue>(cacheKey);
    if (cached) return cached;

    const response = await api.get<GitHubIssue>(`/issues/${number}`);
    setCache(cacheKey, response.data);
    return response.data;
  },

  // Get comments
  getComments: async (number: number): Promise<GitHubComment[]> => {
    const cacheKey = `comments-${config.githubUsername}-${config.githubRepo}-${number}`;
    const cached = getCached<GitHubComment[]>(cacheKey);
    if (cached) return cached;

    const response = await api.get<GitHubComment[]>(`/issues/${number}/comments`);
    setCache(cacheKey, response.data);
    return response.data;
  },

  // Get all labels
  getLabels: async (): Promise<GitHubLabel[]> => {
    const cacheKey = `labels-${config.githubUsername}-${config.githubRepo}`;
    const cached = getCached<GitHubLabel[]>(cacheKey);
    if (cached) return cached;

    const response = await api.get<GitHubLabel[]>('/labels');
    setCache(cacheKey, response.data);
    return response.data;
  },

  // Search issues
  searchIssues: async (query: string): Promise<{ items: GitHubIssue[], total_count: number }> => {
    // Search is dynamic, maybe cache for shorter time or not at all?
    // Let's cache search for 5 mins to prevent repetitive typing queries hitting limits
    const cacheKey = `search-${config.githubUsername}-${config.githubRepo}-${query}`;
    const cached = getCached<{ items: GitHubIssue[], total_count: number }>(cacheKey);
    if (cached) return cached;

    const q = `repo:${config.githubUsername}/${config.githubRepo} type:issue state:open creator:${config.githubUsername} ${query}`;
    const response = await axios.get('https://api.github.com/search/issues', {
      params: { q },
      headers: { Accept: 'application/vnd.github.v3+json' }
    });
    
    setCache(cacheKey, response.data);
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
