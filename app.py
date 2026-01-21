from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import os
import time
from functools import wraps
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import re
import pandas as pd
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import click

# 导入配置和模型
from config import Config
from models import db, Laptop, User, Comment
from sqlalchemy import text

# 导入表单
from forms import LoginForm, RegistrationForm

# 导入高级分析功能
from advanced_analysis import competitive_analysis, price_trend_prediction, sentiment_analysis, laptop_clustering

# 创建应用实例
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录以访问此页面'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """加载用户的回调函数"""
    return db.session.get(User, int(user_id))

_cache_store = {}
def ttl_cache(seconds):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = (fn.__name__, request.query_string.decode())
            now = time.time()
            entry = _cache_store.get(key)
            if entry and entry[1] > now:
                return entry[0]
            rv = fn(*args, **kwargs)
            _cache_store[key] = (rv, now + seconds)
            return rv
        return wrapper
    return deco

# 加载数据函数 - 从数据库加载数据
def load_data():
    """从数据库加载笔记本电脑数据"""
    try:
        laptops = Laptop.query.all()
        print(f"查到数据条数: {len(laptops)}")
        return [laptop.to_dict() for laptop in laptops]
    except Exception as e:
        print(f"加载数据错误: {e}")
        return []

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    # 如果用户已登录，直接重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码错误', 'error')
            return redirect(url_for('login'))
        
        # 登录用户
        login_user(user, remember=form.remember_me.data)
        flash('登录成功！', 'success')
        
        # 获取登录后要重定向的页面
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        return redirect(next_page)
    
    return render_template('login.html', form=form)

# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    # 如果用户已登录，直接重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

# 登出路由
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功登出', 'success')
    return redirect(url_for('login'))

# 首页路由
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# 数据API
@app.route('/api/data')
@login_required
def get_data():
    page = request.args.get('page', type=int)
    page_size = request.args.get('page_size', type=int)
    brand = request.args.get('brand')
    cpu = request.args.get('cpu')
    ram_gb_min = request.args.get('ram_gb_min', type=int)
    ram_gb_max = request.args.get('ram_gb_max', type=int)
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    q = db.session.query(Laptop)
    if brand:
        q = q.filter(Laptop.brand == brand)
    if cpu:
        q = q.filter(Laptop.cpu == cpu)
    if ram_gb_min is not None:
        q = q.filter(Laptop.ram_gb >= ram_gb_min)
    if ram_gb_max is not None:
        q = q.filter(Laptop.ram_gb <= ram_gb_max)
    if price_min is not None:
        q = q.filter(Laptop.price >= price_min)
    if price_max is not None:
        q = q.filter(Laptop.price <= price_max)
    total = q.count()
    if page and page_size:
        items = q.offset((page - 1) * page_size).limit(page_size).all()
    else:
        items = q.all()
    data = [l.to_dict() for l in items]
    return jsonify({'success': True, 'data': data, 'total': total, 'page': page, 'page_size': page_size})

# 总览统计API
@app.route('/api/overview_stats')
@login_required
@ttl_cache(300)
def overview_stats():
    try:
        total_products = db.session.query(db.func.count(Laptop.id)).scalar() or 0
        avg_price = db.session.query(db.func.avg(Laptop.price)).scalar() or 0
        total_sales = db.session.query(db.func.sum(Laptop.sales)).scalar() or 0
        total_brands = db.session.query(db.func.count(db.func.distinct(Laptop.brand))).scalar() or 0
        return jsonify({'success': True, 'data': {
            'total_products': int(total_products),
            'avg_price': float(avg_price),
            'total_sales': int(total_sales),
            'total_brands': int(total_brands)
        }})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 品牌分析API
@app.route('/api/brand_analysis')
@login_required
@ttl_cache(300)
def brand_analysis():
    try:
        # 使用SQLAlchemy进行分组查询
        brand_stats = db.session.query(
            Laptop.brand,
            db.func.count(Laptop.id).label('count'),
            db.func.avg(Laptop.price).label('avg_price'),
            db.func.sum(Laptop.sales).label('total_sales')
        ).group_by(Laptop.brand).all()
        
        result = [{
            'brand': item.brand,
            'count': item.count,
            'avg_price': round(item.avg_price, 2),
            'total_sales': item.total_sales
        } for item in brand_stats]
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# 内存分析API
@app.route('/api/ram_analysis')
@login_required
@ttl_cache(300)
def ram_analysis():
    try:
        ram_stats = db.session.query(
            Laptop.ram_gb,
            db.func.count(Laptop.id).label('count'),
            db.func.avg(Laptop.price).label('avg_price'),
            db.func.sum(Laptop.sales).label('total_sales')
        ).filter(Laptop.ram_gb.isnot(None)).group_by(Laptop.ram_gb).all()
        standardized_data = {}
        for item in ram_stats:
            size = int(item.ram_gb)
            if size <= 4:
                ram_key = "4GB"
            elif size <= 8:
                ram_key = "8GB"
            elif size <= 16:
                ram_key = "16GB"
            elif size <= 32:
                ram_key = "32GB"
            elif size <= 64:
                ram_key = "64GB"
            else:
                ram_key = "128GB+"
            if ram_key in standardized_data:
                standardized_data[ram_key]['count'] += item.count
                standardized_data[ram_key]['total_price'] += item.avg_price * item.count
                standardized_data[ram_key]['total_sales'] += item.total_sales
            else:
                standardized_data[ram_key] = {'count': item.count, 'total_price': item.avg_price * item.count, 'total_sales': item.total_sales}
        result = [{
            'ram': k,
            'count': v['count'],
            'avg_price': round(v['total_price'] / v['count'], 2) if v['count'] > 0 else 0,
            'total_sales': v['total_sales']
        } for k, v in standardized_data.items()]
        ram_order = {"4GB": 1, "8GB": 2, "16GB": 3, "32GB": 4, "64GB": 5, "128GB+": 6}
        result.sort(key=lambda x: ram_order.get(x['ram'], 999))
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# CPU分析API
@app.route('/api/cpu_analysis')
@login_required
@ttl_cache(300)
def cpu_analysis():
    try:
        # 使用SQLAlchemy进行分组查询
        cpu_stats = db.session.query(
            Laptop.cpu,
            db.func.count(Laptop.id).label('count'),
            db.func.avg(Laptop.price).label('avg_price'),
            db.func.sum(Laptop.sales).label('total_sales')
        ).group_by(Laptop.cpu).all()
        
        result = [{
            'cpu': item.cpu,
            'count': item.count,
            'avg_price': round(item.avg_price, 2),
            'total_sales': item.total_sales
        } for item in cpu_stats]
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# 价格区间分析API
@app.route('/api/price_range_analysis')
@login_required
@ttl_cache(300)
def price_range_analysis():
    try:
        # 定义价格区间
        price_ranges = [
            {'min': 0, 'max': 2000, 'label': '0-2000元'},
            {'min': 2000, 'max': 4000, 'label': '2000-4000元'},
            {'min': 4000, 'max': 6000, 'label': '4000-6000元'},
            {'min': 6000, 'max': 8000, 'label': '6000-8000元'},
            {'min': 8000, 'max': 10000, 'label': '8000-10000元'},
            {'min': 10000, 'max': 99999999, 'label': '10000元以上'}
        ]
        
        result = []
        for price_range in price_ranges:
            # 查询每个价格区间的数据
            count = Laptop.query.filter(
                Laptop.price >= price_range['min'],
                Laptop.price < price_range['max']
            ).count()
            
            if count > 0:
                # 计算平均价格
                avg_price = db.session.query(
                    db.func.avg(Laptop.price)
                ).filter(
                    Laptop.price >= price_range['min'],
                    Laptop.price < price_range['max']
                ).scalar()
                
                # 计算总销量
                total_sales = db.session.query(
                    db.func.sum(Laptop.sales)
                ).filter(
                    Laptop.price >= price_range['min'],
                    Laptop.price < price_range['max']
                ).scalar()
                
                result.append({
                    'range': price_range['label'],
                    'count': count,
                    'avg_price': round(avg_price, 2) if avg_price else 0,
                    'total_sales': total_sales if total_sales else 0
                })
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# 销量分析API
@app.route('/api/sales_analysis')
@login_required
@ttl_cache(300)
def sales_analysis():
    try:
        # 获取销量最高的前10个产品
        top_sales = Laptop.query.order_by(Laptop.sales.desc()).limit(10).all()
        top_sales_data = [laptop.to_dict() for laptop in top_sales]
        
        # 获取各品牌的总销量
        brand_sales = db.session.query(
            Laptop.brand,
            db.func.sum(Laptop.sales).label('total_sales')
        ).group_by(Laptop.brand).order_by(db.func.sum(Laptop.sales).desc()).all()
        
        brand_sales_data = [{
            'brand': item.brand,
            'total_sales': item.total_sales
        } for item in brand_sales]
        
        return jsonify({
            'success': True,
            'data': {
                'top_products': top_sales_data,
                'brand_sales': brand_sales_data
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# 价格与销量关系分析API
@app.route('/api/price_sales_correlation')
@login_required
@ttl_cache(300)
def price_sales_correlation():
    try:
        # 获取所有数据
        laptops = Laptop.query.all()
        laptop_dicts = [laptop.to_dict() for laptop in laptops]
        df = pd.DataFrame(laptop_dicts)
        
        # 计算价格与销量的相关系数
        correlation = df['price'].corr(df['sales'])
        
        # 按价格区间分组计算平均销量
        price_bins = [0, 2000, 4000, 6000, 8000, 10000, 99999999]
        price_labels = ['0-2000', '2000-4000', '4000-6000', '6000-8000', '8000-10000', '10000+']        
        df['price_range'] = pd.cut(df['price'], bins=price_bins, labels=price_labels)
        
        price_sales_data = df.groupby('price_range').agg({
            'sales': 'mean',
            'price': 'mean',
            'id': 'count'
        }).reset_index()
        
        price_sales_data = price_sales_data.rename(columns={
            'sales': 'avg_sales',
            'price': 'avg_price',
            'id': 'count'
        })
        
        return jsonify({
            'success': True,
            'data': {
                'correlation': round(correlation, 2),
                'price_sales_data': price_sales_data.to_dict(orient='records')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# 数据导入命令
@app.cli.command('import-csv')
@click.option('--csv_path', default=None, help='Path to the CSV file')
def import_csv(csv_path=None):
    """
    从CSV文件导入数据到MySQL数据库
    :param csv_path: 可选的自定义CSV文件路径
    """
    from migrate_data import migrate_csv_to_mysql
    migrate_csv_to_mysql(csv_path)
    print(f'数据导入完成! 使用的CSV文件: {csv_path or "默认路径"}')

# 初始化数据库命令
@app.cli.command('init-db')
def init_db():
    """初始化数据库，创建所有表"""
    db.create_all()
    print('数据库表已创建!')
    
    # 检查是否有用户，如果没有则创建一个默认管理员
    if User.query.count() == 0:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('已创建默认管理员用户: admin (密码: admin123)')
        print('请登录后立即修改默认密码!')

# 竞品分析API
@app.route('/api/competitive_analysis')
@login_required
def get_competitive_analysis():
    brand = request.args.get('brand')
    return jsonify(competitive_analysis(brand))

# 价格趋势预测API
@app.route('/api/price_trend_prediction')
@login_required
def get_price_trend_prediction():
    brand = request.args.get('brand')
    ram = request.args.get('ram')
    days = request.args.get('days', 30, type=int)
    return jsonify(price_trend_prediction(brand, ram, days))

# 情感分析API
@app.route('/api/sentiment_analysis')
@login_required
def get_sentiment_analysis():
    brand = request.args.get('brand')
    return jsonify(sentiment_analysis(brand))

# 聚类分析API
@app.route('/api/laptop_clustering')
@login_required
def get_laptop_clustering():
    return jsonify(laptop_clustering())

# 新增：返回所有有数据的品牌+内存组合
@app.route('/api/brand_ram_options')
@login_required
def brand_ram_options():
    combos = db.session.query(Laptop.brand, Laptop.ram).group_by(Laptop.brand, Laptop.ram).all()
    result = [{'brand': b, 'ram': r} for b, r in combos]
    return jsonify({'success': True, 'data': result})

@app.cli.command('create-indexes')
def create_indexes():
    stmts = [
        'ALTER TABLE jd ADD INDEX idx_jd_brand (brand)',
        'ALTER TABLE jd ADD INDEX idx_jd_ram (ram)',
        'ALTER TABLE jd ADD INDEX idx_jd_cpu (cpu)',
        'ALTER TABLE jd ADD INDEX idx_jd_price (price)',
        'ALTER TABLE jd ADD INDEX idx_jd_sales (sales)',
        'ALTER TABLE jd ADD INDEX idx_jd_brand_ram (brand, ram)',
        'ALTER TABLE comments ADD INDEX idx_comments_laptop_id (laptop_id)'
    ]
    for s in stmts:
        try:
            db.session.execute(text(s))
            db.session.commit()
        except Exception:
            db.session.rollback()

@app.cli.command('backfill-ram-gb')
def cli_backfill_ram_gb():
    from migrate_data import backfill_ram_gb
    backfill_ram_gb()

# 新增：获取评论数据API
@app.route('/api/comments')
@login_required
def get_comments():
    try:
        # 获取查询参数
        laptop_id = request.args.get('laptop_id', type=int)
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 构建查询
        query = db.session.query(Comment)
        
        # 如果指定了笔记本ID，则只获取该笔记本的评论
        if laptop_id:
            query = query.filter(Comment.laptop_id == laptop_id)
        
        # 获取总数
        total = query.count()
        
        # 分页获取评论
        comments = query.order_by(Comment.created_at.desc()).offset(offset).limit(limit).all()
        
        # 转换为字典列表
        comment_list = [comment.to_dict() for comment in comments]
        
        # 如果指定了笔记本ID，同时返回笔记本信息
        laptop_info = None
        if laptop_id:
            laptop = Laptop.query.get(laptop_id)
            if laptop:
                laptop_info = laptop.to_dict()
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'comments': comment_list,
                'laptop': laptop_info
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# 应用入口
if __name__ == '__main__':
    with app.app_context():
        # 确保数据库表存在
        db.create_all()
    app.run(debug=True)
