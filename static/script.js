let currentFilter = null;

// 標籤篩選功能
function filterByLabel(label) {
    // 更新當前篩選
    currentFilter = label;
    
    // 更新標籤樣式
    document.querySelectorAll('.tag').forEach(tag => {
        tag.classList.remove('active');
        if (tag.getAttribute('data-label') === label) {
            tag.classList.add('active');
        }
    });
    
    // 顯示清除篩選按鈕
    document.getElementById('clear-filter').classList.add('visible');
    
    // 更新篩選信息
    const labelName = document.querySelector(`.tag[data-label="${label}"]`).textContent;
    document.getElementById('filter-info').textContent = `當前篩選: ${labelName}`;
    
    // 顯示/隱藏分類
    let hasResults = false;
    document.querySelectorAll('.category-section').forEach(section => {
        if (section.getAttribute('data-label') === label) {
            section.style.display = 'block';
            hasResults = true;
        } else {
            section.style.display = 'none';
        }
    });
    
    // 顯示/隱藏無結果提示
    document.getElementById('no-results').style.display = hasResults ? 'none' : 'block';
    
    // 隱藏最近文章列表
    const recentArticlesSection = document.querySelector('.category-section h2').parentNode;
    if (recentArticlesSection && recentArticlesSection.querySelector('h2').textContent.includes('最近文章')) {
        recentArticlesSection.style.display = 'none';
    }
}

// 清除篩選
function clearFilter() {
    currentFilter = null;
    
    // 移除標籤激活狀態
    document.querySelectorAll('.tag').forEach(tag => {
        tag.classList.remove('active');
    });
    
    // 隱藏清除篩選按鈕
    document.getElementById('clear-filter').classList.remove('visible');
    
    // 重置篩選信息
    document.getElementById('filter-info').textContent = '點擊標籤篩選文章';
    
    // 顯示所有分類
    document.querySelectorAll('.category-section').forEach(section => {
        section.style.display = 'block';
    });
    
    // 隱藏無結果提示
    document.getElementById('no-results').style.display = 'none';
    
    // 顯示最近文章列表
    const recentArticlesSection = document.querySelector('.category-section h2').parentNode;
    if (recentArticlesSection && recentArticlesSection.querySelector('h2').textContent.includes('最近文章')) {
        recentArticlesSection.style.display = 'block';
    }
}

// 顯示更多文章
function toggleMore(categoryId) {
    const hiddenDiv = document.getElementById('hidden-' + categoryId);
    const btn = document.getElementById('btn-' + categoryId);
    
    if (hiddenDiv.classList.contains('visible')) {
        hiddenDiv.classList.remove('visible');
        const itemCount = hiddenDiv.querySelectorAll('li').length;
        btn.textContent = `顯示更多 (${itemCount}篇)`;
    } else {
        hiddenDiv.classList.add('visible');
        btn.textContent = '顯示更少';
    }
}

// ========== 導航欄交互功能 ==========

// 導航菜單切換（移動端）
function toggleMobileMenu() {
    const navLinks = document.getElementById('nav-links');
    const menuToggle = document.getElementById('menu-toggle');
    
    if (navLinks && menuToggle) {
        navLinks.classList.toggle('active');
        const isActive = navLinks.classList.contains('active');
        menuToggle.innerHTML = isActive ? '✕' : '☰';
        menuToggle.setAttribute('aria-expanded', isActive ? 'true' : 'false');
    }
}

// 關閉移動端菜單
function closeMobileMenu() {
    const navLinks = document.getElementById('nav-links');
    const menuToggle = document.getElementById('menu-toggle');
    
    if (navLinks && menuToggle && navLinks.classList.contains('active')) {
        navLinks.classList.remove('active');
        menuToggle.innerHTML = '☰';
        menuToggle.setAttribute('aria-expanded', 'false');
    }
}

// 設置當前頁面激活狀態
function setActiveNavLink() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        // 移除所有active類
        link.classList.remove('active');
        
        // 設置當前頁面active
        if (href === currentPage || 
            (currentPage === '' && href === 'index.html') ||
            (currentPage === 'index.html' && href === 'index.html')) {
            link.classList.add('active');
        }
        
        // 為外部鏈接添加target="_blank"
        if (href.startsWith('http')) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        }
    });
}

// 監聽滾動，為導航欄添加陰影
function handleNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 10) {
            navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        } else {
            navbar.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
        }
    }
}

// ========== 頁面加載完成後初始化 ==========
document.addEventListener('DOMContentLoaded', function() {
    console.log('頁面加載完成，初始化功能...');
    
    // 綁定清除篩選按鈕事件
    const clearFilterBtn = document.getElementById('clear-filter');
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', clearFilter);
        console.log('清除篩選按鈕綁定成功');
    }
    
    // 綁定標籤點擊事件
    document.querySelectorAll('.tag').forEach(tag => {
        tag.addEventListener('click', function() {
            const label = this.getAttribute('data-label');
            if (label) {
                filterByLabel(label);
                closeMobileMenu(); // 篩選後關閉移動端菜單
            }
        });
    });
    
    // 綁定顯示更多按鈕事件
    document.querySelectorAll('.show-more-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const categoryId = this.id.replace('btn-', '');
            toggleMore(categoryId);
        });
    });
    
    // ========== 導航欄初始化 ==========
    
    // 綁定移動端菜單按鈕
    const menuToggle = document.getElementById('menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', toggleMobileMenu);
        console.log('移動端菜單按鈕綁定成功');
    }
    
    // 設置當前頁面激活狀態
    setActiveNavLink();
    console.log('導航鏈接激活狀態設置完成');
    
    // 綁定導航鏈接點擊事件（關閉移動端菜單）
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            // 如果是站內鏈接且不是當前頁面，等待一小段時間後關閉菜單
            const href = this.getAttribute('href');
            if (!href.startsWith('http') && !this.classList.contains('active')) {
                setTimeout(closeMobileMenu, 300);
            }
            // 外部鏈接已在新標籤頁打開，不需要額外處理
        });
    });
    
    // 綁定滾動事件
    window.addEventListener('scroll', handleNavbarScroll);
    // 初始化滾動狀態
    handleNavbarScroll();
    
    // 點擊頁面其他區域關閉移動端菜單
    document.addEventListener('click', function(e) {
        const navLinks = document.getElementById('nav-links');
        const menuToggle = document.getElementById('menu-toggle');
        
        if (navLinks && navLinks.classList.contains('active') &&
            !navLinks.contains(e.target) && 
            menuToggle && !menuToggle.contains(e.target)) {
            closeMobileMenu();
        }
    });
    
    // ESC鍵關閉移動端菜單
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeMobileMenu();
        }
    });
    
    console.log('所有功能初始化完成！');
});

// ========== 導出函數供全局使用 ==========
// 確保函數可以在HTML的onclick屬性中使用
if (typeof window !== 'undefined') {
    window.filterByLabel = filterByLabel;
    window.clearFilter = clearFilter;
    window.toggleMore = toggleMore;
    window.toggleMobileMenu = toggleMobileMenu;
}
