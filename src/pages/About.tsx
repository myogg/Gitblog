import { Link } from "wouter";

export default function About() {
  const links = [
    { url: 'https://829259.xyz', name: '829259.xyz', desc: "mymsnn'blog" },
    { url: 'https://jianghaiyina.com', name: 'jianghaiyina.com', desc: "Jaaleng'blog" },
    { url: 'https://jreely.dpdns.org', name: 'jreely.dpdns.org', desc: '北方' },
    { url: 'https://tel.qzz.io', name: 'tel.qzz.io', desc: '书签' },
    { url: 'https://myogg.hidns.co', name: 'myogg.hidns.co', desc: "meektion'blog" }
  ];

  return (
    <div className="markdown-body" style={{ maxWidth: '700px', margin: '0 auto', background: 'transparent' }}>
      
      
      <div className="about-container text-center my-8 md:mb-16">
        <div className="w-[150px] h-[150px] mx-auto mb-8 rounded-full overflow-hidden border-4 border-[#f0f0f0] bg-[#f9f9f9]">
          <img 
            src="https://pic.imgdd.cc/item/68975648abb08ec37a9cd5e8.png" 
            alt="我的照片" 
            className="w-full h-full object-cover"
          />
        </div>
        <div className="max-w-[600px] mx-auto mb-16 leading-loose text-[#555] text-lg px-5">
          <p className="mb-4">用文字记录我的胡思乱想与生活的瞬间，我疯狂的想法与可能为之的行動。</p>
          <p>记录在这个时代下的焦虑、迷茫、挣扎与希望。</p>
        </div>
      </div>
      
      <div className="category-section">
        <h2 className="section-label text-sm font-medium text-[#666] uppercase mb-4 border-none p-0">🔗 友情链接</h2>
        <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-4 mt-5">
          {links.map((link) => (
            <a 
              key={link.url}
              href={link.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="no-underline p-4 bg-[#f9f9f9] rounded-lg border border-[#eee] transition-all duration-300 hover:-translate-y-1 block"
            >
              <div className="font-semibold text-[#1a1a1a] text-sm mb-1">{link.name}</div>
              <div className="text-[#888] text-xs">{link.desc}</div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
