import { useEffect, useRef } from 'react';
import { init } from '@waline/client';
// @ts-ignore
import '@waline/client/style';
import { useTheme } from '@/contexts/ThemeContext';

interface WalineCommentProps {
  path: string;
}

export default function WalineComment({ path }: WalineCommentProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();
  const walineInstanceRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    walineInstanceRef.current = init({
      el: containerRef.current,
      serverURL: 'https://waline.134688.xyz',
      path: path,
      lang: 'zh-CN',
      dark: theme === 'dark',
      login: 'disable',
      meta: ['nick'],
      requiredMeta: ['nick'],
      pageSize: 10,
      pageview: true,
      comment: true,
      reaction: true,
    });

    return () => {
      if (walineInstanceRef.current) {
        walineInstanceRef.current.destroy();
      }
    };
  }, [path]);

  // Update dark mode dynamically
  useEffect(() => {
    if (walineInstanceRef.current) {
      walineInstanceRef.current.update({
        dark: theme === 'dark',
      });
    }
  }, [theme]);

  return <div ref={containerRef} className="mt-12 pt-8" />;
}
