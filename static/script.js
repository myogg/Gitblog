[file name]: script.js
[file content begin]
let currentFilter = null;

// 標籤篩選功能 - 支持時間流
function filterByLabel(label) {
    console.log('篩選標籤:', label); // 調試信息
    
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
    
    // 4. 執行時間流過濾邏輯 - 修復版
    const sections = document.querySelectorAll('.category-section');
    let anySectionVisible = false;
    let anyArticleVisible = false;
    
    sections.forEach(section => {
        // 先隱藏整個分類，然後逐個檢查文章
        section.style.display = 'none';
        
        const articles = section.querySelectorAll('.article-item');
        let sectionHasVisibleArticles = false;
        
        // 檢查分類中的每一篇文章
        articles.forEach(article => {
            const articleLabels = article.getAttribute('data-labels');
            
            // 如果文章包含該標籤，顯示這篇文章
            if (articleLabels && articleLabels.indexOf(label) !== -1) {
                article.style.display = '';
                sectionHasVisibleArticles = true;
                anyArticleVisible = true;
            } else {
                article.style.display = 'none';
            }
        });
        
        // 如果分類中有可見的文章，顯示整個分類
        if (sectionHasVisibleArticles) {
            section.style.display = 'block';
            anySectionVisible = true;
        }
    });
    
    console.log('有顯示的分類?', anySectionVisible);
    console.log('有顯示的文章?', anyArticleVisible);
    
    // 如果沒有任何文章符合，顯示提示
    if (!anyArticleVisible) {
        showNoResultsMessage(label);
    } else {
        removeNoResultsMessage();
        
        // 平滑滾動到內容區頂部
        const container = document.getElementById('categories-container');
        if (container) {
            // 先滾動到頁面頂部，再滾動到分類容器
            window.scrollTo({ top: 0, behavior: 'smooth' });
            setTimeout(() => {
                container.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 300);
        }
    }
}

// 顯示無結果提示
function showNoResultsMessage(label) {
    // 移除現有的提示
    removeNoResultsMessage();
    
    // 創建提示元素
    const message = document.createElement('div');
    message.id = 'no-results-message';
    message.className = 'no-results-message';
    message.innerHTML = `
        <p>沒有找到標籤為 "<strong>${getLabelName(label)}</strong>" 的文章</p>
        <p><button onclick="clearFilter()">顯示所有文章</button></p>
    `;
    
    // 插入到分類容器前
    const container = document.getElementById('categories-container');
    if (container && container.parentNode) {
        container.parentNode.insertBefore(message, container);
    }
}

// 移除無結果提示
function removeNoResultsMessage() {
    const existing = document.getElementById('no-results-message');
    if (existing) {
        existing.remove();
    }
}

// 根據安全名稱獲取原始標籤名稱
function getLabelName(safeName) {
    const tags = document.querySelectorAll('.tag');
    for (const tag of tags) {
        if (tag.getAttribute('data-label') === safeName) {
            return tag.textContent.trim();
        }
    }
    return safeName;
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
    
    // 3. 移除無結果提示
    removeNoResultsMessage();
    
    // 4. 顯示所有月份分類和所有文章
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
    
    // 調試：檢查所有標籤
    console.log('頁面加載完成，檢查標籤:');
    document.querySelectorAll('.tag').forEach(tag => {
        console.log('標籤:', tag.textContent, 'data-label:', tag.getAttribute('data-label'));
    });
    
    // 調試：檢查第一篇文章的標籤
    const firstArticle = document.querySelector('.article-item');
    if (firstArticle) {
        console.log('第一篇文章標籤:', firstArticle.getAttribute('data-labels'));
    }
    
    // 調試：檢查所有分類的標籤
    console.log('檢查分類標籤:');
    document.querySelectorAll('.category-section').forEach(section => {
        console.log('分類:', section.querySelector('h2')?.textContent, 
                    'data-labels:', section.getAttribute('data-labels'));
    });
});
[file content end]
