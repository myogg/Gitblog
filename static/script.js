let currentFilter = null;

// 標籤篩選功能 - 支持時間流
function filterByLabel(label) {
    // 1. 更新當前篩選狀態
    currentFilter = label;
    
    // 2. 更新標籤樣式 (選中狀態)
    document.querySelectorAll('.tag').forEach(tag => {
        if (tag.getAttribute('data-label') === label) {
            tag.style.opacity = "1";
            tag.style.outline = "2px solid #0366d6";
        } else {
            tag.style.opacity = "0.6";
            tag.style.outline = "none";
        }
    });
    
    // 3. 顯示清除篩選按鈕
    const clearBtn = document.getElementById('clear-filter');
    if (clearBtn) clearBtn.style.display = 'inline';
    
    // 4. 執行時間流過濾邏輯
    const sections = document.querySelectorAll('.category-section');
    sections.forEach(section => {
        const sectionLabels = section.getAttribute('data-labels');
        
        if (sectionLabels && sectionLabels.includes(label)) {
            // 顯示該月份分類
            section.style.display = 'block';
            
            // 篩選該月份內的文章
            const articles = section.querySelectorAll('.article-item');
            articles.forEach(article => {
                const articleLabels = article.getAttribute('data-labels');
                if (articleLabels && articleLabels.includes(label)) {
                    article.style.display = '';
                } else {
                    article.style.display = 'none';
                }
            });
        } else {
            // 隱藏沒有該標籤的月份分類
            section.style.display = 'none';
        }
    });

    // 平滑滾動到內容區頂部
    const container = document.getElementById('categories-container');
    if (container) container.scrollIntoView({ behavior: 'smooth' });
}

// 清除篩選功能 - 支持時間流
function clearFilter() {
    currentFilter = null;
    
    // 1. 恢復標籤外觀
    document.querySelectorAll('.tag').forEach(tag => {
        tag.style.opacity = "1";
        tag.style.outline = "none";
    });
    
    // 2. 隱藏清除按鈕
    const clearBtn = document.getElementById('clear-filter');
    if (clearBtn) clearBtn.style.display = 'none';
    
    // 3. 顯示所有月份分類和所有文章
    document.querySelectorAll('.category-section').forEach(section => {
        section.style.display = 'block';
        
        // 顯示該分類內的所有文章
        const articles = section.querySelectorAll('.article-item');
        articles.forEach(article => {
            article.style.display = '';
        });
    });
}

// 顯示更多文章切換 - 保留但不影響時間流
function toggleMore(categoryId) {
    // 對應 base.html 裡的 id="hidden-{{safe_name}}-hidden"
    const hiddenDiv = document.getElementById('hidden-' + categoryId);
    const btn = document.getElementById('btn-' + categoryId);
    
    if (!hiddenDiv || !btn) return;

    if (hiddenDiv.style.display === 'block') {
        hiddenDiv.style.display = 'none';
        btn.textContent = '顯示更多';
    } else {
        hiddenDiv.style.display = 'block';
        btn.textContent = '顯示更少';
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    const clearFilterBtn = document.getElementById('clear-filter');
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', clearFilter);
    }
});
