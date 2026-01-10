import type { BlogConfig } from './types';

export const config: BlogConfig = {
  githubUsername: import.meta.env.VITE_GITHUB_USERNAME || 'myogg',
  githubRepo: import.meta.env.VITE_GITHUB_REPO || 'Gitblog',
  title: import.meta.env.VITE_BLOG_TITLE || '北方的博客',
  description: import.meta.env.VITE_BLOG_DESC || '70后的分享，记录技术、生活和思考。探索编程、人工智能、个人成长等话题。',
  author: import.meta.env.VITE_BLOG_AUTHOR || 'Jiang Sheng',
  pageSize: Number(import.meta.env.VITE_PAGE_SIZE) || 10,
};

// Labels to ignore in the list view if needed (e.g. 'Friends' or 'About')
export const IGNORE_LABELS = ['Friends', 'About', 'TODO'];

// Special labels mapping
export const SPECIAL_LABELS = {
  FRIENDS: 'Friends',
  ABOUT: 'About',
};
