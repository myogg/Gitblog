// ============================================
// 主题切换功能
// ============================================
function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;

    const htmlEl = document.documentElement;
    const bodyEl = document.body;

    // 从 localStorage 读取主题
    const savedTheme = localStorage.getItem('theme') || 'light';
    bodyEl.setAttribute('data-theme', savedTheme);
    if (savedTheme === 'dark') {
        htmlEl.classList.add('dark');
    } else {
        htmlEl.classList.remove('dark');
    }

    themeToggle.addEventListener('click', () => {
        const currentTheme = bodyEl.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        bodyEl.setAttribute('data-theme', newTheme);
        
        if (newTheme === 'dark') {
            htmlEl.classList.add('dark');
        } else {
            htmlEl.classList.remove('dark');
        }
        
        localStorage.setItem('theme', newTheme);
    });
}

// ============================================
// 下拉菜单功能
// ============================================
function initDropdown() {
    const menuToggle = document.getElementById('menuToggle');
    const dropdownMenu = document.getElementById('dropdownMenu');
    
    if (!menuToggle || !dropdownMenu) return;

    menuToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownMenu.classList.toggle('show');
    });

    document.addEventListener('click', () => {
        dropdownMenu.classList.remove('show');
    });
}

// ============================================
// 滚动时 header 样式变化
// ============================================
function initHeaderScroll() {
    const header = document.querySelector('.site-header');
    if (!header) return;

    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 10) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
}

// ============================================
// 返回顶部功能
// ============================================
function initBackToTop() {
    const backToTopButton = document.getElementById('backToTop');
    if (!backToTopButton) return;

    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTopButton.classList.add('show');
        } else {
            backToTopButton.classList.remove('show');
        }
    });

    backToTopButton.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// ============================================
// 复制 RSS 地址（供全局调用）
// ============================================
window.copyRssUrl = function(event) {
    const urlInput = document.getElementById('rssUrl');
    if (!urlInput) return;
    
    urlInput.select();
    urlInput.setSelectionRange(0, 99999);

    const btn = event?.target || document.querySelector('.subscribe-button');
    const originalText = btn.textContent;
    
    navigator.clipboard.writeText(urlInput.value).then(() => {
        btn.textContent = '已复制!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }).catch(() => {
        // 兼容旧浏览器
        document.execCommand('copy');
        btn.textContent = '已复制!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    });
};

// ============================================
// 初始化所有功能
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initDropdown();
    initHeaderScroll();
    initBackToTop();
});
