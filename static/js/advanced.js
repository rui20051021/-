// 高级分析功能JavaScript

// 页面加载完成后执行
$(document).ready(function() {
    // 高级分析标签页切换
    const advancedTabs = document.querySelectorAll('#advanced-tabs button');
    advancedTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 移除所有标签页的活动状态
            advancedTabs.forEach(t => {
                t.classList.remove('tab-active');
                t.classList.add('text-gray-500');
            });
            
            // 添加当前标签页的活动状态
            this.classList.add('tab-active');
            this.classList.remove('text-gray-500');
            
            // 隐藏所有内容
            document.querySelectorAll('#advanced .tab-content').forEach(content => {
                content.classList.add('hidden');
            });
            
            // 显示当前内容
            const tabId = this.getAttribute('data-tab');
            document.getElementById(`${tabId}-content`).classList.remove('hidden');
        });
    });
    
    // 初始化品牌下拉菜单
    initBrandDropdowns();
    
    // 竞品分析按钮点击事件
    $('#competitive-analyze-btn').click(function() {
        const brand = $('#competitive-brand').val();
        if (!brand) {
            alert('请选择品牌');
            return;
        }
        analyzeCompetitors(brand);
    });
    
    // 价格趋势预测按钮点击事件
    $('#trend-analyze-btn').click(function() {
        const brand = $('#trend-brand').val();
        const ram = $('#trend-ram').val();
        const days = $('#trend-days').val();
        predictPriceTrend(brand, ram, days);
    });
    
    // 情感分析按钮点击事件
    $('#sentiment-analyze-btn').click(function() {
        const brand = $('#sentiment-brand').val();
        analyzeSentiment(brand);
    });
    
    // 聚类分析按钮点击事件
    $('#clustering-analyze-btn').click(function() {
        analyzeClustering();
    });
    
    // 初始化内存下拉菜单
    initRamDropdown();
});

// 初始化品牌下拉菜单
function initBrandDropdowns() {
    $.ajax({
        url: '/api/brand_analysis',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                const brands = response.data;
                // 按品牌名称排序
                brands.sort((a, b) => a.brand.localeCompare(b.brand));
                
                // 填充所有品牌下拉菜单
                const dropdowns = ['#competitive-brand', '#trend-brand', '#sentiment-brand'];
                dropdowns.forEach(dropdown => {
                    const select = $(dropdown);
                    select.find('option:not(:first)').remove(); // 清除现有选项，保留第一个
                    
                    brands.forEach(brand => {
                        select.append(`<option value="${brand.brand}">${brand.brand}</option>`);
                    });
                });
            }
        },
        error: function(error) {
            console.error('获取品牌数据失败:', error);
        }
    });
}

// 初始化内存下拉菜单
function initRamDropdown() {
    $.ajax({
        url: '/api/ram_analysis',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                const ramData = response.data;
                // 按内存大小排序（提取数字部分）
                ramData.sort((a, b) => {
                    const aNum = parseInt(a.ram.match(/\d+/)[0]);
                    const bNum = parseInt(b.ram.match(/\d+/)[0]);
                    return aNum - bNum;
                });
                
                // 填充内存下拉菜单
                const select = $('#trend-ram');
                select.find('option:not(:first)').remove(); // 清除现有选项，保留第一个
                
                ramData.forEach(ram => {
                    select.append(`<option value="${ram.ram}">${ram.ram}</option>`);
                });
            }
        },
        error: function(error) {
            console.error('获取内存数据失败:', error);
        }
    });
}

// 竞品分析
function analyzeCompetitors(brand) {
    // 显示加载状态
    $('#competitive-loading').removeClass('hidden');
    $('#competitive-result').addClass('hidden');
    
    $.ajax({
        url: `/api/competitive_analysis?brand=${encodeURIComponent(brand)}`,
        method: 'GET',
        success: function(response) {
            // 隐藏加载状态
            $('#competitive-loading').addClass('hidden');
            
            if (response.success) {
                const data = response.data;
                
                // 显示目标品牌数据
                $('#target-product-count').text(data.target_count || 0);
                $('#target-avg-price').text(`¥${data.target_avg_price || 0}`);
                $('#target-total-sales').text((data.target_total_sales || 0).toLocaleString());
                // 新增：显示市场份额
                if (data.target_total_sales && data.total_market_sales) {
                    const marketShare = (data.target_total_sales / data.total_market_sales * 100).toFixed(1);
                    $('#target-market-share').text(marketShare + '%');
                } else {
                    $('#target-market-share').text('--');
                }
                
                // 清空并填充竞争对手容器
                const competitorsContainer = $('#competitors-container');
                competitorsContainer.empty();
                
                if (data.competitors && data.competitors.length > 0) {
                    data.competitors.forEach(competitor => {
                        // 创建竞争对手卡片
                        const competitorCard = $(`
                            <div class="competitor-card">
                                <div class="competitor-header">
                                    <div class="competitor-name">${competitor.brand}</div>
                                    <div class="text-sm text-gray-600">${competitor.count} 款产品</div>
                                </div>
                                <div class="competitor-stats">
                                    <div class="competitor-stat">
                                        <div class="competitor-stat-value">¥${competitor.avg_price}</div>
                                        <div class="competitor-stat-label">平均价格</div>
                                        <div class="text-sm ${competitor.price_diff_percent > 0 ? 'diff-positive' : 'diff-negative'}">
                                            ${competitor.price_diff_percent > 0 ? '+' : ''}${competitor.price_diff_percent}%
                                        </div>
                                    </div>
                                    <div class="competitor-stat">
                                        <div class="competitor-stat-value">${competitor.total_sales.toLocaleString()}</div>
                                        <div class="competitor-stat-label">总销量</div>
                                        <div class="text-sm ${competitor.sales_diff_percent > 0 ? 'diff-positive' : 'diff-negative'}">
                                            ${competitor.sales_diff_percent > 0 ? '+' : ''}${competitor.sales_diff_percent}%
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `);
                        
                        competitorsContainer.append(competitorCard);
                    });
                } else {
                    competitorsContainer.html('<p class="text-center text-gray-600 py-4">没有找到竞争对手数据</p>');
                }
                
                // 显示结果
                $('#competitive-result').removeClass('hidden');
            } else {
                alert(`分析失败: ${response.message || '未知错误'}`);
            }
        },
        error: function(error) {
            $('#competitive-loading').addClass('hidden');
            alert('请求失败，请稍后再试');
            console.error('竞品分析请求失败:', error);
        }
    });
}

// 价格趋势预测
function predictPriceTrend(brand, ram, days) {
    // 显示加载状态
    $('#trend-loading').removeClass('hidden');
    $('#trend-result').addClass('hidden');
    
    // 构建查询参数
    let queryParams = [];
    if (brand) queryParams.push(`brand=${encodeURIComponent(brand)}`);
    if (ram) queryParams.push(`ram=${encodeURIComponent(ram)}`);
    if (days) queryParams.push(`days=${days}`);
    
    $.ajax({
        url: `/api/price_trend_prediction?${queryParams.join('&')}`,
        method: 'GET',
        success: function(response) {
            // 隐藏加载状态
            $('#trend-loading').addClass('hidden');
            
            if (response.success) {
                const data = response.data;
                
                // 新增：无数据友好提示
                if (data.current_avg_price === 0) {
                    alert('该品牌和内存组合没有足够的数据，无法预测价格趋势，请更换条件。');
                    return;
                }
                
                // 更新筛选信息
                let filterInfo = '全部数据';
                if (data.filter.brand) {
                    filterInfo = `品牌: ${data.filter.brand}`;
                    if (data.filter.ram) {
                        filterInfo += `, 内存: ${data.filter.ram}`;
                    }
                }
                $('#trend-filter-info').text(filterInfo);
                
                // 更新趋势分析数据
                $('#trend-current-price').text(`¥${data.current_avg_price}`);
                $('#trend-predicted-price').text(`¥${data.trend_analysis.end_price}`);
                $('#trend-change-percent').text(`${data.trend_analysis.change_percent > 0 ? '+' : ''}${data.trend_analysis.change_percent}%`);
                
                // 设置趋势方向
                let trendDirection = '稳定';
                let trendClass = 'text-yellow-500';
                if (data.trend_analysis.trend === 'rising') {
                    trendDirection = '上涨';
                    trendClass = 'text-red-500';
                } else if (data.trend_analysis.trend === 'falling') {
                    trendDirection = '下降';
                    trendClass = 'text-green-500';
                }
                $('#trend-direction').text(trendDirection).removeClass().addClass(trendClass);
                
                // 创建价格趋势图表
                createPriceTrendChart(data.price_data);
                
                // 显示结果
                $('#trend-result').removeClass('hidden');
            } else {
                alert(`预测失败: ${response.message || '未知错误'}`);
            }
        },
        error: function(error) {
            $('#trend-loading').addClass('hidden');
            alert('请求失败，请稍后再试');
            console.error('价格趋势预测请求失败:', error);
        }
    });
}

// 创建价格趋势图表
function createPriceTrendChart(priceData) {
    // 准备图表数据
    const labels = [];
    const historicalData = [];
    const predictionData = [];
    const lowerData = [];
    const upperData = [];
    
    // 处理历史数据
    priceData.historical.forEach(item => {
        labels.push(item.date);
        historicalData.push(item.price);
        predictionData.push(null);
        lowerData.push(null);
        upperData.push(null);
    });
    
    // 处理预测数据
    priceData.prediction.forEach(item => {
        labels.push(item.date);
        historicalData.push(null);
        predictionData.push(item.price);
        lowerData.push(item.lower);
        upperData.push(item.upper);
    });
    
    // 销毁现有图表
    if (window.priceTrendChart && typeof window.priceTrendChart.destroy === 'function') {
        window.priceTrendChart.destroy();
    }
    
    // 创建新图表，增加置信区间带
    const ctx = document.getElementById('priceTrendChart').getContext('2d');
    window.priceTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '历史价格',
                    data: historicalData,
                    borderColor: '#4361ee',
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    tension: 0.3,
                    fill: false
                },
                {
                    label: '预测价格',
                    data: predictionData,
                    borderColor: '#f72585',
                    backgroundColor: 'rgba(247, 37, 133, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 3,
                    tension: 0.3,
                    fill: false
                },
                {
                    label: '预测区间',
                    data: upperData,
                    borderColor: 'rgba(247,37,133,0.0)',
                    backgroundColor: 'rgba(247,37,133,0.08)',
                    pointRadius: 0,
                    borderWidth: 0,
                    fill: '-1', // 填充到下一个数据集（即lowerData）
                    order: 1
                },
                {
                    label: '',
                    data: lowerData,
                    borderColor: 'rgba(247,37,133,0.0)',
                    backgroundColor: 'rgba(247,37,133,0.08)',
                    pointRadius: 0,
                    borderWidth: 0,
                    fill: false,
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '价格趋势预测',
                    font: { size: 16, weight: 'bold' }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.label === '预测区间') return null;
                            if (context.datasetIndex === 2) return null;
                            if (context.datasetIndex === 3) return null;
                            return `¥${context.raw}`;
                        }
                    }
                },
                legend: { display: true }
            },
            scales: {
                x: { title: { display: true, text: '日期' } },
                y: { title: { display: true, text: '价格 (元)' } }
            }
        }
    });
}

// 情感分析
function analyzeSentiment(brand) {
    // 显示加载状态
    $('#sentiment-loading').removeClass('hidden');
    $('#sentiment-result').addClass('hidden');
    
    // 构建查询参数
    let queryParams = [];
    if (brand) queryParams.push(`brand=${encodeURIComponent(brand)}`);
    
    $.ajax({
        url: `/api/sentiment_analysis?${queryParams.join('&')}`,
        method: 'GET',
        success: function(response) {
            // 隐藏加载状态
            $('#sentiment-loading').addClass('hidden');
            
            if (response.success) {
                const data = response.data;
                
                // 更新筛选信息
                let filterInfo = '全部评价';
                if (data.filter.brand) {
                    filterInfo = `品牌: ${data.filter.brand}`;
                }
                $('#sentiment-filter-info').text(filterInfo);
                
                // 更新情感分析数据
                $('#sentiment-score-value').text(data.sentiment_score);
                $('#sentiment-total-reviews').text(data.total_reviews.toLocaleString());
                
                // 更新情感分布
                const positivePercent = data.sentiment_distribution.positive.percentage;
                const neutralPercent = data.sentiment_distribution.neutral.percentage;
                const negativePercent = data.sentiment_distribution.negative.percentage;
                
                $('#sentiment-positive-percent').text(`${positivePercent}%`);
                $('#sentiment-neutral-percent').text(`${neutralPercent}%`);
                $('#sentiment-negative-percent').text(`${negativePercent}%`);
                
                $('#sentiment-positive-bar').css('width', `${positivePercent}%`);
                $('#sentiment-neutral-bar').css('width', `${neutralPercent}%`);
                $('#sentiment-negative-bar').css('width', `${negativePercent}%`);
                
                // 更新关键词
                const positiveKeywords = $('#positive-keywords');
                const negativeKeywords = $('#negative-keywords');
                
                positiveKeywords.empty();
                negativeKeywords.empty();
                
                data.keywords.positive.forEach(keyword => {
                    positiveKeywords.append(`
                        <span class="keyword-tag positive">
                            ${keyword.keyword} (${keyword.count})
                        </span>
                    `);
                });
                
                data.keywords.negative.forEach(keyword => {
                    negativeKeywords.append(`
                        <span class="keyword-tag negative">
                            ${keyword.keyword} (${keyword.count})
                        </span>
                    `);
                });
                
                // 显示结果
                $('#sentiment-result').removeClass('hidden');
            } else {
                alert(`分析失败: ${response.message || '未知错误'}`);
            }
        },
        error: function(error) {
            $('#sentiment-loading').addClass('hidden');
            alert('请求失败，请稍后再试');
            console.error('情感分析请求失败:', error);
        }
    });
}

// 聚类分析
function analyzeClustering() {
    // 显示加载状态
    $('#clustering-loading').removeClass('hidden');
    $('#clustering-result').addClass('hidden');
    
    $.ajax({
        url: '/api/laptop_clustering',
        method: 'GET',
        success: function(response) {
            // 隐藏加载状态
            $('#clustering-loading').addClass('hidden');
            
            if (response.success) {
                const data = response.data;
                
                // 更新聚类数量
                $('#cluster-count').text(data.best_k);
                
                // 创建聚类图表
                createClusteringChart(data);
                
                // 清空并填充聚类容器
                const clustersContainer = $('#clusters-container');
                clustersContainer.empty();
                
                if (data.clusters && data.clusters.length > 0) {
                    data.clusters.forEach(cluster => {
                        // 确定聚类徽章样式
                        let badgeClass = 'cluster-badge ';
                        if (cluster.segment === '经济实惠型') {
                            badgeClass += 'economy';
                        } else if (cluster.segment === '高端豪华型') {
                            badgeClass += 'premium';
                        } else {
                            badgeClass += 'mainstream';
                        }
                        
                        // 创建聚类卡片
                        const clusterCard = $(`
                            <div class="cluster-card">
                                <div class="cluster-header">
                                    <div class="cluster-title">聚类 ${cluster.cluster_id + 1}</div>
                                    <div class="${badgeClass}">${cluster.segment}</div>
                                </div>
                                <p class="text-sm text-gray-600 mb-4">
                                    该聚类包含 ${cluster.size} 款产品，占总数的 ${cluster.percentage}%
                                </p>
                                <div class="cluster-stats">
                                    <div class="cluster-stat">
                                        <div class="cluster-stat-value">¥${cluster.avg_price}</div>
                                        <div class="cluster-stat-label">平均价格</div>
                                    </div>
                                    <div class="cluster-stat">
                                        <div class="cluster-stat-value">${cluster.avg_sales.toFixed(0)}</div>
                                        <div class="cluster-stat-label">平均销量</div>
                                    </div>
                                    <div class="cluster-stat">
                                        <div class="cluster-stat-value">${cluster.avg_ram}GB</div>
                                        <div class="cluster-stat-label">平均内存</div>
                                    </div>
                                    <div class="cluster-stat">
                                        <div class="cluster-stat-value">${cluster.popularity}</div>
                                        <div class="cluster-stat-label">受欢迎程度</div>
                                    </div>
                                </div>
                                <div class="top-brands mt-4">
                                    <h5 class="font-medium mb-2">主要品牌</h5>
                                    <div id="cluster-${cluster.cluster_id}-brands"></div>
                                </div>
                            </div>
                        `);
                        
                        clustersContainer.append(clusterCard);
                        
                        // 添加主要品牌
                        const brandsContainer = $(`#cluster-${cluster.cluster_id}-brands`);
                        Object.entries(cluster.top_brands).forEach(([brand, count]) => {
                            brandsContainer.append(`
                                <span class="brand-pill">
                                    ${brand} (${count})
                                </span>
                            `);
                        });
                    });
                } else {
                    clustersContainer.html('<p class="text-center text-gray-600 py-4">没有找到聚类数据</p>');
                }
                
                // 显示结果
                $('#clustering-result').removeClass('hidden');
            } else {
                alert(`分析失败: ${response.message || '未知错误'}`);
            }
        },
        error: function(error) {
            $('#clustering-loading').addClass('hidden');
            alert('请求失败，请稍后再试');
            console.error('聚类分析请求失败:', error);
        }
    });
}

// 创建聚类图表
function createClusteringChart(data) {
    // 准备图表数据
    const clusters = data.clusters;
    const labels = clusters.map(c => c.segment);
    const sizes = clusters.map(c => c.size);
    const avgPrices = clusters.map(c => c.avg_price);
    
    // 销毁现有图表
    if (window.clusteringChart && typeof window.clusteringChart.destroy === 'function') {
        window.clusteringChart.destroy();
    }
    
    // 创建新图表
    const ctx = document.getElementById('clusteringChart').getContext('2d');
    window.clusteringChart = new Chart(ctx, {
        type: 'bubble',
        data: {
            datasets: clusters.map((cluster, index) => {
                // 为不同聚类设置不同颜色
                const colors = ['#4361ee', '#f72585', '#4cc9f0', '#f8961e', '#43aa8b'];
                const color = colors[index % colors.length];
                
                return {
                    label: `${cluster.segment} (${cluster.size}款)`,
                    data: [{
                        x: cluster.avg_price,
                        y: cluster.avg_sales,
                        r: Math.sqrt(cluster.size) * 3 // 气泡大小与聚类大小成比例
                    }],
                    backgroundColor: `${color}4D`, // 添加透明度
                    borderColor: color,
                    borderWidth: 1
                };
            })
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const cluster = clusters[context.datasetIndex];
                            return [
                                `${cluster.segment}`,
                                `产品数量: ${cluster.size}`,
                                `平均价格: ¥${cluster.avg_price}`,
                                `平均销量: ${cluster.avg_sales.toFixed(0)}`,
                                `平均内存: ${cluster.avg_ram}GB`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '平均价格 (¥)'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '平均销量'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

let brandRamOptions = [];

// 页面加载时获取所有有数据的品牌+内存组合
$.get('/api/brand_ram_options', function(res) {
    if (res.success) {
        brandRamOptions = res.data;
        // 填充品牌下拉框
        const brands = [...new Set(brandRamOptions.map(item => item.brand))];
        const brandSelect = $('#trend-brand');
        brandSelect.find('option:not(:first)').remove();
        brands.forEach(brand => {
            brandSelect.append(`<option value="${brand}">${brand}</option>`);
        });
    }
});

// 品牌下拉框change事件，自动刷新内存下拉框
$('#trend-brand').on('change', function() {
    const selectedBrand = $(this).val();
    const rams = brandRamOptions.filter(item => item.brand === selectedBrand).map(item => item.ram);
    const ramSelect = $('#trend-ram');
    ramSelect.find('option:not(:first)').remove();
    rams.forEach(ram => {
        ramSelect.append(`<option value="${ram}">${ram}</option>`);
    });
});