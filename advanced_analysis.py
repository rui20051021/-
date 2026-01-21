# 高级分析功能模块
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from models import db, Laptop, Comment
import re
import time

# 竞品分析功能
def competitive_analysis(brand=None):
    """
    对指定品牌的笔记本电脑进行竞品分析
    :param brand: 品牌名称，如果为None则分析所有品牌
    :return: 竞品分析结果
    """
    try:
        # 基础查询
        query = Laptop.query
        
        # 如果指定了品牌，则筛选该品牌的数据
        if brand:
            target_brand_data = query.filter(Laptop.brand == brand).all()
            # 获取该品牌的平均价格
            avg_price = sum(laptop.price for laptop in target_brand_data) / len(target_brand_data) if target_brand_data else 0
            # 获取价格相近的其他品牌产品（价格范围：目标品牌平均价格的±20%）
            price_min = avg_price * 0.8
            price_max = avg_price * 1.2
            competitors = query.filter(Laptop.brand != brand, 
                                      Laptop.price >= price_min, 
                                      Laptop.price <= price_max).all()
            
            # 计算竞品分析结果
            total_market_sales = db.session.query(db.func.sum(Laptop.sales)).scalar() or 0
            result = {
                'target_brand': brand,
                'target_count': len(target_brand_data),
                'target_avg_price': round(avg_price, 2),
                'target_total_sales': sum(laptop.sales for laptop in target_brand_data),
                'total_market_sales': total_market_sales,
                'competitors': []
            }
            
            # 按品牌分组竞品数据
            competitor_brands = {}
            for laptop in competitors:
                if laptop.brand not in competitor_brands:
                    competitor_brands[laptop.brand] = {
                        'brand': laptop.brand,
                        'count': 0,
                        'total_price': 0,
                        'total_sales': 0
                    }
                competitor_brands[laptop.brand]['count'] += 1
                competitor_brands[laptop.brand]['total_price'] += laptop.price
                competitor_brands[laptop.brand]['total_sales'] += laptop.sales
            
            # 计算平均价格并添加到结果中
            for brand_name, data in competitor_brands.items():
                data['avg_price'] = round(data['total_price'] / data['count'], 2)
                # 计算价格差异百分比
                data['price_diff_percent'] = round((data['avg_price'] - avg_price) / avg_price * 100, 2)
                # 计算销量差异百分比
                target_avg_sales = result['target_total_sales'] / result['target_count'] if result['target_count'] > 0 else 0
                competitor_avg_sales = data['total_sales'] / data['count']
                data['sales_diff_percent'] = round((competitor_avg_sales - target_avg_sales) / target_avg_sales * 100, 2) if target_avg_sales > 0 else 0
                # 添加到结果列表
                result['competitors'].append({
                    'brand': brand_name,
                    'count': data['count'],
                    'avg_price': data['avg_price'],
                    'total_sales': data['total_sales'],
                    'price_diff_percent': data['price_diff_percent'],
                    'sales_diff_percent': data['sales_diff_percent']
                })
            
            # 按销量排序竞品列表
            result['competitors'].sort(key=lambda x: x['total_sales'], reverse=True)
            
            return {
                'success': True,
                'data': result
            }
        else:
            # 如果没有指定品牌，则返回所有品牌的基本信息
            all_brands = db.session.query(Laptop.brand, 
                                         db.func.count(Laptop.id).label('count'),
                                         db.func.avg(Laptop.price).label('avg_price'),
                                         db.func.sum(Laptop.sales).label('total_sales')
                                        ).group_by(Laptop.brand).all()
            
            brands_data = [{
                'brand': item.brand,
                'count': item.count,
                'avg_price': round(item.avg_price, 2),
                'total_sales': item.total_sales
            } for item in all_brands]
            
            # 按销量排序
            brands_data.sort(key=lambda x: x['total_sales'], reverse=True)
            
            return {
                'success': True,
                'data': brands_data
            }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

# 价格趋势预测功能
def price_trend_prediction(brand=None, ram=None, days=30):
    """
    预测未来价格趋势，增强波动性，生成置信区间，每次预测都不一样
    :param brand: 品牌名称
    :param ram: 内存大小
    :param days: 预测天数
    :return: 价格趋势预测结果
    """
    try:
        # 用品牌、内存和当前时间混合生成随机种子
        seed_str = f"{brand}_{ram}_{time.time()}"
        seed = abs(hash(seed_str)) % (2**32 - 1)
        np.random.seed(seed)
        query = Laptop.query
        if brand:
            query = query.filter(Laptop.brand == brand)
        if ram:
            query = query.filter(Laptop.ram == ram)
        current_avg_price = db.session.query(db.func.avg(Laptop.price)).filter(query.whereclause).scalar() or 0
        past_days = 90
        dates = pd.date_range(end=pd.Timestamp.now(), periods=past_days).tolist()
        trend = np.linspace(0.95, 1.0, past_days)
        seasonality = 0.08 * np.sin(np.linspace(0, 6*np.pi, past_days))
        noise = np.random.normal(0, 0.04, past_days)
        historical_prices = current_avg_price * (trend + seasonality + noise)
        historical_data = pd.DataFrame({
            'date': dates,
            'price': historical_prices
        })
        historical_data['day_of_week'] = historical_data['date'].dt.dayofweek
        historical_data['day_of_month'] = historical_data['date'].dt.day
        historical_data['month'] = historical_data['date'].dt.month
        historical_data['days_from_start'] = range(past_days)
        X = historical_data[['days_from_start']].values
        poly = PolynomialFeatures(degree=2)
        X_poly = poly.fit_transform(X)
        model = LinearRegression()
        model.fit(X_poly, historical_data['price'])
        future_dates = pd.date_range(start=pd.Timestamp.now(), periods=days+1)[1:].tolist()
        future_days_from_start = range(past_days, past_days + days)
        X_future = poly.transform(np.array(future_days_from_start).reshape(-1, 1))
        predicted_prices = model.predict(X_future)
        future_seasonality = 0.08 * np.sin(np.linspace(0, 6*np.pi, days))
        future_noise = np.random.normal(0, 0.06, days)
        predicted_prices = predicted_prices * (1 + future_seasonality + future_noise)
        lower = predicted_prices * 0.93
        upper = predicted_prices * 1.07
        prediction_data = {
            'historical': [{
                'date': date.strftime('%Y-%m-%d'),
                'price': round(price, 2)
            } for date, price in zip(dates[-30:], historical_prices[-30:])],
            'prediction': [{
                'date': date.strftime('%Y-%m-%d'),
                'price': round(price, 2),
                'lower': round(l, 2),
                'upper': round(u, 2)
            } for date, price, l, u in zip(future_dates, predicted_prices, lower, upper)]
        }
        first_predicted_price = predicted_prices[0]
        last_predicted_price = predicted_prices[-1]
        price_change = last_predicted_price - first_predicted_price
        price_change_percent = (price_change / first_predicted_price) * 100 if first_predicted_price > 0 else 0
        trend_analysis = {
            'start_price': round(first_predicted_price, 2),
            'end_price': round(last_predicted_price, 2),
            'change': round(price_change, 2),
            'change_percent': round(price_change_percent, 2),
            'trend': 'rising' if price_change > 0 else 'falling' if price_change < 0 else 'stable'
        }
        return {
            'success': True,
            'data': {
                'price_data': prediction_data,
                'trend_analysis': trend_analysis,
                'current_avg_price': round(current_avg_price, 2),
                'filter': {
                    'brand': brand,
                    'ram': ram
                }
            }
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

# 用户评价情感分析（模拟功能）
def sentiment_analysis(brand=None):
    """
    对用户评价进行情感分析（模拟功能）
    :param brand: 品牌名称
    :return: 情感分析结果
    
    """
    try:
        # 构建查询条件
        query = Laptop.query
        if brand:
            query = query.filter(Laptop.brand == brand)
            
        # 获取笔记本电脑数据
        laptops = query.all()
        laptop_count = len(laptops)
        
        if laptop_count == 0:
            return {
                'success': False,
                'message': '没有找到符合条件的数据'
            }
        
        # 模拟情感分析结果
        # 在实际应用中，这部分应该从评论数据库中获取并进行NLP处理
        np.random.seed(abs(hash(brand)) % (2**32 - 1) if brand else 42)  # 根据品牌设置随机种子，保证seed合法
        
        # 生成模拟的情感分析结果
        positive_ratio = np.random.uniform(0.6, 0.9)  # 积极评价比例
        neutral_ratio = np.random.uniform(0.05, 0.2)  # 中性评价比例
        negative_ratio = 1 - positive_ratio - neutral_ratio  # 消极评价比例
        
        # 获取实际评价总数
        # 首先获取该品牌所有笔记本的ID
        laptop_ids = [laptop.id for laptop in laptops]
        # 然后查询这些笔记本对应的评论数量
        total_reviews = db.session.query(Comment).filter(Comment.laptop_id.in_(laptop_ids)).count()
        positive_count = int(total_reviews * positive_ratio)
        neutral_count = int(total_reviews * neutral_ratio)
        negative_count = total_reviews - positive_count - neutral_count
        
        # 模拟常见评价关键词
        positive_keywords = {
            '性能好': np.random.randint(positive_count // 4, positive_count // 2),
            '外观漂亮': np.random.randint(positive_count // 5, positive_count // 3),
            '性价比高': np.random.randint(positive_count // 6, positive_count // 3),
            '散热好': np.random.randint(positive_count // 8, positive_count // 4),
            '屏幕清晰': np.random.randint(positive_count // 7, positive_count // 3)
        }
        
        negative_keywords = {
            '价格贵': np.random.randint(negative_count // 5, negative_count // 2),
            '续航差': np.random.randint(negative_count // 6, negative_count // 3),
            '散热差': np.random.randint(negative_count // 7, negative_count // 3),
            '噪音大': np.random.randint(negative_count // 8, negative_count // 4),
            '配置低': np.random.randint(negative_count // 9, negative_count // 4)
        }
        
        # 计算情感得分（0-100）
        sentiment_score = int(positive_ratio * 100)
        
        # 生成情感分析结果
        result = {
            'total_reviews': total_reviews,
            'sentiment_distribution': {
                'positive': {
                    'count': positive_count,
                    'percentage': round(positive_ratio * 100, 2)
                },
                'neutral': {
                    'count': neutral_count,
                    'percentage': round(neutral_ratio * 100, 2)
                },
                'negative': {
                    'count': negative_count,
                    'percentage': round(negative_ratio * 100, 2)
                }
            },
            'sentiment_score': sentiment_score,
            'keywords': {
                'positive': [{'keyword': k, 'count': v} for k, v in positive_keywords.items()],
                'negative': [{'keyword': k, 'count': v} for k, v in negative_keywords.items()]
            },
            'filter': {
                'brand': brand
            }
        }
        
        return {
            'success': True,
            'data': result
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

# 用户评价情感分析（基于实际数据）
def sentiment_analysis(brand=None):
    """
    对用户评价进行情感分析（基于实际数据）
    :param brand: 品牌名称
    :return: 情感分析结果
    """
    try:
        # 构建查询条件
        query = Laptop.query
        if brand:
            query = query.filter(Laptop.brand == brand)

        # 获取笔记本电脑数据
        laptops = query.all()
        laptop_count = len(laptops)

        if laptop_count == 0:
            return {
                'success': False,
                'message': '没有找到符合条件的数据'
            }

        # 获取实际评价总数
        laptop_ids = [laptop.id for laptop in laptops]
        total_reviews = db.session.query(Comment).filter(Comment.laptop_id.in_(laptop_ids)).count()

        # 使用NLP库进行情感分析
        # 假设我们有一个函数`perform_sentiment_analysis`来处理评论文本并返回情感结果
        sentiment_results = perform_sentiment_analysis(laptop_ids)

        positive_count = sentiment_results['positive']
        neutral_count = sentiment_results['neutral']
        negative_count = sentiment_results['negative']

        # 计算情感得分（0-100）
        sentiment_score = int((positive_count / total_reviews) * 100)

        # 生成情感分析结果
        result = {
            'total_reviews': total_reviews,
            'sentiment_distribution': {
                'positive': {
                    'count': positive_count,
                    'percentage': round((positive_count / total_reviews) * 100, 2)
                },
                'neutral': {
                    'count': neutral_count,
                    'percentage': round((neutral_count / total_reviews) * 100, 2)
                },
                'negative': {
                    'count': negative_count,
                    'percentage': round((negative_count / total_reviews) * 100, 2)
                }
            },
            'sentiment_score': sentiment_score,
            'filter': {
                'brand': brand
            }
        }

        return {
            'success': True,
            'data': result
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

# 笔记本电脑聚类分析
def laptop_clustering():
    """
    对笔记本电脑进行聚类分析，找出市场细分
    :return: 聚类分析结果
    """
    try:
        # 获取所有笔记本电脑数据
        laptops = Laptop.query.all()
        laptop_dicts = [laptop.to_dict() for laptop in laptops]
        df = pd.DataFrame(laptop_dicts)
        
        # 只保留有效数据
        df = df[(df['price'].notnull()) & (df['price'] > 0) & (df['sales'].notnull())]
        
        if len(df) < 10:
            return {
                'success': False,
                'message': '有效数据量太少，无法进行聚类分析'
            }
        
        # 提取数值特征
        # 从RAM字段中提取数字（假设格式为"16GB"）
        df['ram_value'] = df['ram'].apply(lambda x: int(re.search(r'\d+', str(x)).group()) if pd.notnull(x) and re.search(r'\d+', str(x)) else 0)
        
        # 准备聚类特征
        features = df[['price', 'sales', 'ram_value']].copy()
        
        # 标准化特征
        features_scaled = (features - features.mean()) / features.std()
        
        # 确定最佳聚类数
        silhouette_scores = []
        K_range = range(2, 6)
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42)
            cluster_labels = kmeans.fit_predict(features_scaled)
            silhouette_avg = silhouette_score(features_scaled, cluster_labels)
            silhouette_scores.append(silhouette_avg)
        
        # 选择最佳聚类数
        best_k = K_range[silhouette_scores.index(max(silhouette_scores))]
        
        # 使用最佳聚类数进行聚类
        kmeans = KMeans(n_clusters=best_k, random_state=42)
        df['cluster'] = kmeans.fit_predict(features_scaled)
        
        # 分析每个聚类
        cluster_analysis = []
        for i in range(best_k):
            cluster_df = df[df['cluster'] == i]
            
            # 计算该聚类的特征统计
            cluster_info = {
                'cluster_id': i,
                'size': len(cluster_df),
                'percentage': round(len(cluster_df) / len(df) * 100, 2),
                'avg_price': round(cluster_df['price'].mean(), 2),
                'avg_sales': round(cluster_df['sales'].mean(), 2),
                'avg_ram': round(cluster_df['ram_value'].mean(), 2),
                'price_range': {
                    'min': round(cluster_df['price'].min(), 2),
                    'max': round(cluster_df['price'].max(), 2)
                },
                'top_brands': cluster_df['brand'].value_counts().head(3).to_dict()
            }
            
            # 确定聚类特点
            if cluster_info['avg_price'] < df['price'].mean() * 0.7:
                cluster_info['segment'] = '经济实惠型'
            elif cluster_info['avg_price'] > df['price'].mean() * 1.3:
                cluster_info['segment'] = '高端豪华型'
            else:
                cluster_info['segment'] = '中端主流型'
                
            if cluster_info['avg_sales'] > df['sales'].mean() * 1.2:
                cluster_info['popularity'] = '热销'
            elif cluster_info['avg_sales'] < df['sales'].mean() * 0.8:
                cluster_info['popularity'] = '冷门'
            else:
                cluster_info['popularity'] = '一般'
                
            cluster_analysis.append(cluster_info)
        
        # 按聚类大小排序
        cluster_analysis.sort(key=lambda x: x['size'], reverse=True)
        
        return {
            'success': True,
            'data': {
                'clusters': cluster_analysis,
                'best_k': best_k,
                'silhouette_scores': dict(zip([str(k) for k in K_range], silhouette_scores))
            }
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }