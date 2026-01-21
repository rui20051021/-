// 全局图表变量
let priceDistributionChart = null;
let brandMarketShareChart = null;
let priceSalesRelationshipChart = null;
let ramDistributionChart = null;
let cpuDistributionChart = null;
let predictionComparisonChart = null;

// 页面加载完成后执行
$(document).ready(function() {
    // 移动端菜单切换
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    mobileMenuButton.addEventListener('click', function() {
        mobileMenu.classList.toggle('hidden');
    });
    
    // 平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
                
                // 如果是移动端，点击后关闭菜单
                if (!mobileMenu.classList.contains('hidden')) {
                    mobileMenu.classList.add('hidden');
                }
            }
        });
    });
    
    // 滚动时改变导航栏样式
    window.addEventListener('scroll', function() {
        const header = document.getElementById('main-header');
        if (window.scrollY > 10) {
            header.classList.add('py-2');
            header.classList.remove('py-3');
        } else {
            header.classList.add('py-3');
            header.classList.remove('py-2');
        }
    });
    
    // 图表标签页切换
    const chartTabs = document.querySelectorAll('#chart-tabs button');
    chartTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 移除所有标签页的活动状态
            chartTabs.forEach(t => {
                t.classList.remove('tab-active');
                t.classList.add('text-gray-500');
            });
            
            // 添加当前标签页的活动状态
            this.classList.add('tab-active');
            this.classList.remove('text-gray-500');
            
            // 隐藏所有内容
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
            });
            
            // 显示当前内容
            const tabId = this.getAttribute('data-tab');
            document.getElementById(`${tabId}-content`).classList.remove('hidden');
        });
    });
    
    // 开始分析按钮点击事件
    $('#analyze-button').click(function() {
        startAnalysis();
    });
});

// 开始分析
function startAnalysis() {
    const loadingInfo = document.getElementById('loading-info');
    const analyzeProgress = document.getElementById('analyze-progress');
    const analyzeStatus = document.getElementById('analyze-status');
    
    loadingInfo.classList.remove('hidden');
    
    // 模拟进度
    let progress = 0;
    const interval = setInterval(() => {
        progress += 10;
        analyzeProgress.style.width = `${progress}%`;
        
        if (progress < 30) {
            analyzeStatus.textContent = '正在加载数据...';
        } else if (progress < 60) {
            analyzeStatus.textContent = '正在进行统计分析...';
        } else if (progress < 90) {
            analyzeStatus.textContent = '正在生成可视化图表...';
        } else {
            analyzeStatus.textContent = '正在训练预测模型...';
        }
        
        if (progress >= 100) {
            clearInterval(interval);
            analyzeStatus.textContent = '分析完成！';
            
            // 显示所有分析区域
            document.querySelectorAll('section').forEach(section => {
                if (section.id !== 'overview') {
                    section.classList.remove('hidden');
                }
            });
            
            // 获取统计数据
            fetchStatistics();
            
            // 获取图表数据并创建图表
            fetchChartData();
            
            // 平滑滚动到数据概览区域
            setTimeout(() => {
                document.querySelector('#statistics').scrollIntoView({
                    behavior: 'smooth'
                });
            }, 500);
        }
    }, 200);
}

// 获取统计数据
function fetchStatistics() {
    // 使用总览统计接口，避免全量数据加载
    $.ajax({
        url: '/api/overview_stats',
        method: 'GET',
        success: function(resp) {
            let stats = { total_products: 0, avg_price: 0, total_sales: 0, total_brands: 0 };
            if (resp && resp.success && resp.data) {
                stats = resp.data;
            }
            $.ajax({
                url: '/api/brand_analysis',
                method: 'GET',
                success: function(res) {
                    let brand_stats = [];
                    if (res && res.success) {
                        brand_stats = res.data.map(item => ({
                            brand: item.brand,
                            product_count: item.count,
                            avg_price: item.avg_price,
                            total_sales: item.total_sales
                        }));
                    }
                    displayBasicStatistics(stats, brand_stats);
                },
                error: function() {
                    displayBasicStatistics(stats, []);
                }
            });
        },
        error: function() {
            displayBasicStatistics({ total_products: 0, avg_price: 0, total_sales: 0, total_brands: 0 }, []);
        }
    });
}

// 显示基本统计信息
function displayBasicStatistics(stats, brandStats) {
    // 总商品数
    $('#total-products').text(stats.total_products);
    
    // 平均价格
    $('#avg-price').text(`¥${stats.avg_price.toFixed(2)}`);
    
    // 总销量
    $('#total-sales').text(stats.total_sales.toLocaleString());
    
    // 品牌数量
    $('#total-brands').text(stats.total_brands);
    
    // 品牌表格
    const brandTableBody = $('#brand-table-body');
    brandTableBody.empty();
    
    if (brandStats && brandStats.length > 0) {
        // 计算总销量
        const totalSales = brandStats.reduce((sum, brand) => sum + Number(brand.total_sales), 0);
        
        // 填充表格
        brandStats.forEach(brand => {
            let marketShare = '--';
            if (totalSales > 0 && Number(brand.total_sales) > 0) {
                marketShare = (Number(brand.total_sales) / totalSales * 100).toFixed(1) + '%';
            }
            const row = `
                <tr class="border-b border-gray-200 hover:bg-gray-50 transition-colors duration-150">
                    <td class="py-3 px-4">${brand.brand}</td>
                    <td class="py-3 px-4">${brand.product_count}</td>
                    <td class="py-3 px-4">¥${brand.avg_price.toFixed(2)}</td>
                    <td class="py-3 px-4">${brand.total_sales.toLocaleString()}</td>
                    <td class="py-3 px-4">
                        <div class="flex items-center">
                            <div class="w-full bg-gray-200 rounded-full h-2.5 mr-2">
                                <div class="bg-blue-600 h-2.5 rounded-full" style="width: ${marketShare === '--' ? '0' : marketShare}"></div>
                            </div>
                            <span class="text-sm">${marketShare}</span>
                        </div>
                    </td>
                </tr>
            `;
            
            brandTableBody.append(row);
        });
    }
}

// 获取图表数据并创建图表
function fetchChartData() {
    // 价格分布
    $.ajax({
        url: '/api/price_range_analysis',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                const labels = response.data.map(item => item.range);
                const data = response.data.map(item => item.count);
                createPriceDistributionChart(labels, data);
            }
        }
    });
    // 品牌分布
    $.ajax({
        url: '/api/brand_analysis',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                const labels = response.data.map(item => item.brand);
                // 保证销量为数字类型
                const data = response.data.map(item => Number(item.total_sales));
                createBrandMarketShareChart(labels, data);
            }
        }
    });
    // 价格与销量关系
    $.ajax({
        url: '/api/price_sales_correlation',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                // 转换为散点图格式
                const data = response.data.price_sales_data.map(item => ({ x: item.avg_price, y: item.avg_sales }));
                createPriceSalesRelationshipChart(data);
            }
        }
    });
    // 内存分布
    $.ajax({
        url: '/api/ram_analysis',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                // 对内存数据进行处理和排序
                const ramData = response.data.map(item => ({
                    ram: item.ram,
                    count: item.count,
                    // 提取内存大小的数字部分用于排序
                    size: parseInt(item.ram.match(/\d+/)[0] || 0)
                }));
                
                // 按内存大小排序
                ramData.sort((a, b) => a.size - b.size);
                
                const labels = ramData.map(item => item.ram);
                const data = ramData.map(item => item.count);
                createRamDistributionChart(labels, data);
            }
        }
    });
    // CPU分布
    $.ajax({
        url: '/api/cpu_analysis',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                const labels = response.data.map(item => item.cpu);
                const data = response.data.map(item => item.count);
                createCpuDistributionChart(labels, data);
            }
        }
    });
}

// 创建价格分布图表
function createPriceDistributionChart(labels, data) {
    const ctx = document.getElementById('priceDistributionChart').getContext('2d');
    if (priceDistributionChart) priceDistributionChart.destroy();
    if (!data || data.length === 0) {
        ctx.canvas.parentNode.innerHTML = '<div class="text-center text-gray-400 py-20">暂无数据</div>';
        return;
    }
    priceDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '商品数量',
                data: data,
                backgroundColor: 'rgba(37, 99, 235, 0.6)',
                borderColor: 'rgba(37, 99, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '笔记本电脑价格分布',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `商品数量: ${context.raw}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '价格区间 (元)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '商品数量'
                    }
                }
            }
        }
    });
}

// 创建品牌市场份额图表
function createBrandMarketShareChart(labels, data) {
    const ctx = document.getElementById('brandMarketShareChart').getContext('2d');
    if (brandMarketShareChart) brandMarketShareChart.destroy();
    if (!data || data.length === 0) {
        ctx.canvas.parentNode.innerHTML = '<div class="text-center text-gray-400 py-20">暂无数据</div>';
        return;
    }
    // 自动扩展颜色数组
    const baseColors = [
        'rgba(37, 99, 235, 0.6)',   // 蓝色
        'rgba(6, 182, 212, 0.6)',    // 青色
        'rgba(16, 185, 129, 0.6)',   // 绿色
        'rgba(245, 158, 11, 0.6)',   // 琥珀色
        'rgba(239, 68, 68, 0.6)',    // 红色
        'rgba(139, 92, 246, 0.6)',   // 紫色
        'rgba(5, 150, 105, 0.6)',    // 翡翠绿
        'rgba(251, 146, 60, 0.6)',   // 橙色
        'rgba(107, 114, 128, 0.6)'   // 灰色
    ];
    let colors = [];
    while (colors.length < labels.length) {
        colors = colors.concat(baseColors);
    }
    colors = colors.slice(0, labels.length);
    
    brandMarketShareChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 1,
                hoverOffset: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '品牌市场份额 (按销量)',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

// 创建价格与销量关系图表
function createPriceSalesRelationshipChart(data) {
    const ctx = document.getElementById('priceSalesRelationshipChart').getContext('2d');
    if (priceSalesRelationshipChart) priceSalesRelationshipChart.destroy();
    if (!data || data.length === 0) {
        ctx.canvas.parentNode.innerHTML = '<div class="text-center text-gray-400 py-20">暂无数据</div>';
        return;
    }
    priceSalesRelationshipChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: '笔记本电脑',
                data: data,
                backgroundColor: 'rgba(37, 99, 235, 0.5)',
                borderColor: 'rgba(37, 99, 235, 1)',
                borderWidth: 1,
                pointRadius: 4,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '价格与销量关系',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return [
                                `价格: ¥${context.parsed.x.toFixed(2)}`,
                                `销量: ${context.parsed.y.toLocaleString()}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '价格 (元)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '销量'
                    }
                }
            }
        }
    });
}

// 创建内存分布图表
function createRamDistributionChart(labels, data) {
    const ctx = document.getElementById('ramDistributionChart').getContext('2d');
    if (ramDistributionChart) ramDistributionChart.destroy();
    if (!data || data.length === 0) {
        ctx.canvas.parentNode.innerHTML = '<div class="text-center text-gray-400 py-20">暂无数据</div>';
        return;
    }
    ramDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '商品数量',
                data: data,
                backgroundColor: 'rgba(14, 165, 233, 0.6)',
                borderColor: 'rgba(14, 165, 233, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '笔记本电脑内存分布',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `商品数量: ${context.raw}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '内存容量'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '商品数量'
                    },
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// 创建CPU分布图表
function createCpuDistributionChart(labels, data) {
    const ctx = document.getElementById('cpuDistributionChart').getContext('2d');
    if (cpuDistributionChart) cpuDistributionChart.destroy();
    if (!data || data.length === 0) {
        ctx.canvas.parentNode.innerHTML = '<div class="text-center text-gray-400 py-20">暂无数据</div>';
        return;
    }
    cpuDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '商品数量',
                data: data,
                backgroundColor: 'rgba(139, 92, 246, 0.6)',
                borderColor: 'rgba(139, 92, 246, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '笔记本电脑CPU分布',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'CPU类型'
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '商品数量'
                    }
                }
            }
        }
    });
}

// 用户评价情感分析
$('#sentiment-analyze-btn').click(function() {
    const brand = $('#sentiment-brand').val();
    if (!brand) {
        alert('请选择品牌');
        return;
    }
    
    $('#sentiment-loading').removeClass('hidden');
    $('#sentiment-result').addClass('hidden');
    
    // 获取情感分析数据
    $.ajax({
        url: '/api/sentiment_analysis',
        method: 'GET',
        data: { brand: brand },
        success: function(response) {
            $('#sentiment-loading').addClass('hidden');
            $('#sentiment-result').removeClass('hidden');
            
            if (response.success) {
                const data = response.data;
                
                // 更新情感分析数据
                $('#sentiment-filter-info').text(`品牌: ${brand}`);
                $('#sentiment-score-value').text(data.sentiment_score.toFixed(1));
                $('#sentiment-total-reviews').text(data.total_reviews.toLocaleString());
                
                // 更新情感分布
                $('#sentiment-positive-percent').text(`${data.positive_percent.toFixed(1)}%`);
                $('#sentiment-positive-bar').css('width', `${data.positive_percent}%`);
                
                $('#sentiment-neutral-percent').text(`${data.neutral_percent.toFixed(1)}%`);
                $('#sentiment-neutral-bar').css('width', `${data.neutral_percent}%`);
                
                $('#sentiment-negative-percent').text(`${data.negative_percent.toFixed(1)}%`);
                $('#sentiment-negative-bar').css('width', `${data.negative_percent}%`);
                
                // 更新关键词
                updateKeywords(data.positive_keywords, '#positive-keywords');
                updateKeywords(data.negative_keywords, '#negative-keywords');
                
                // 新增：获取并显示评分数据
                $.ajax({
                    url: '/api/get_data',
                    method: 'GET',
                    data: { brand: brand },
                    success: function(ratingResponse) {
                        if (ratingResponse.success) {
                            // 计算平均评分
                            let totalRating = 0;
                            let count = 0;
                            
                            ratingResponse.data.forEach(laptop => {
                                if (laptop.rating > 0) {
                                    totalRating += laptop.rating;
                                    count++;
                                }
                            });
                            
                            const avgRating = count > 0 ? (totalRating / count).toFixed(1) : '--';
                            
                            // 更新评分显示
                            $('#average-rating-value').text(avgRating);
                            
                            // 更新星星显示
                            updateRatingStars(avgRating);
                        }
                    }
                });
            } else {
                alert('获取情感分析数据失败: ' + response.message);
            }
        },
        error: function(xhr, status, error) {
            $('#sentiment-loading').addClass('hidden');
            alert('获取情感分析数据出错: ' + error);
        }
    });
});

// 新增：更新评分星星显示
function updateRatingStars(rating) {
    if (rating === '--') return;
    
    const ratingValue = parseFloat(rating);
    const fullStars = Math.floor(ratingValue);
    const hasHalfStar = ratingValue - fullStars >= 0.5;
    
    let starsHtml = '';
    
    // 添加实心星星
    for (let i = 0; i < fullStars; i++) {
        starsHtml += '<i class="fa fa-star text-yellow-500 text-xl mx-1"></i>';
    }
    
    // 添加半星（如果需要）
    if (hasHalfStar) {
        starsHtml += '<i class="fa fa-star-half-alt text-yellow-500 text-xl mx-1"></i>';
    }
    
    // 添加空心星星
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    for (let i = 0; i < emptyStars; i++) {
        starsHtml += '<i class="fa fa-star text-gray-300 text-xl mx-1"></i>';
    }
    
    $('#rating-stars').html(starsHtml);
}
