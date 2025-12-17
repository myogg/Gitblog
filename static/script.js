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
    document.getElementById('recent-articles').parentNode.style.display = 'none';
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
    document.getElementById('recent-articles').parentNode.style.display = 'block';
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

// 頁面加載完成後初始化
document.addEventListener('DOMContentLoaded', function() {
    // 綁定清除篩選按鈕事件
    const clearFilterBtn = document.getElementById('clear-filter');
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', clearFilter);
    }
});
