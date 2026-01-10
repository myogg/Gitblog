import { Link } from "wouter";
import notFoundImg from "@/assets/404.png";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <img 
        src={notFoundImg} 
        alt="404 Lost" 
        className="w-full max-w-md mb-8 animate-in zoom-in duration-500" 
      />
      <h1 className="text-4xl font-bold mb-4">404 - 页面未找到</h1>
      <p className="text-muted-foreground mb-8 max-w-md">
        你似乎迷路了。这个页面可能已经被删除，或者你输入的地址有误。
      </p>
      <Link href="/">
        <Button size="lg">返回首页</Button>
      </Link>
    </div>
  );
}
