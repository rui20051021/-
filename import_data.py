# 简化版数据导入脚本
import os
import pandas as pd
import re
import random
from flask import Flask
from models import db, Laptop, Comment
from config import Config

# 创建应用实例
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

# 根据评论内容生成评分的函数
def generate_rating_from_comment(comment):
    """根据评论内容生成评分（1-5分）"""
    if not comment or pd.isna(comment) or not comment.strip():
        return random.uniform(3.0, 4.0)  # 如果没有评论，给一个随机的中等评分
    
    # 正面评价关键词
    positive_keywords = ['好', '优秀', '满意', '推荐', '喜欢', '不错', '高性能', '性价比高', '值得', '快', '强劲']
    # 负面评价关键词
    negative_keywords = ['差', '不好', '失望', '退货', '慢', '卡顿', '问题', '缺点', '贵', '不值']
    
    # 计算正面和负面关键词出现的次数
    positive_count = sum(1 for keyword in positive_keywords if keyword in comment)
    negative_count = sum(1 for keyword in negative_keywords if keyword in comment)
    
    # 基础评分为3分
    base_rating = 3.0
    
    # 根据正面和负面关键词调整评分
    rating = base_rating + (positive_count * 0.5) - (negative_count * 0.5)
    
    # 确保评分在1-5之间
    rating = max(1.0, min(5.0, rating))
    
    # 添加一些随机性
    rating += random.uniform(-0.2, 0.2)
    rating = max(1.0, min(5.0, round(rating, 1)))
    
    return rating

def import_csv_to_mysql():
    """将CSV数据导入到MySQL数据库"""
    with app.app_context():
        # 创建数据库表
        db.create_all()
        
        # 删除跳过导入的逻辑，确保每次都执行数据同步
        # existing_count = Laptop.query.count()
        # if existing_count > 0:
        #     print(f'数据库中已有 {existing_count} 条数据，跳过导入')
        #     return
        
        # 读取CSV文件，自动尝试多种编码
        csv_path = os.path.join(app.static_folder, 'data', '笔记本电脑_final.csv')
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'utf-8-sig']
        for enc in encodings:
            try:
                df = pd.read_csv(csv_path, encoding=enc)
                print(f'成功用 {enc} 编码读取CSV文件，共 {len(df)} 条数据')
                break
            except Exception as e:
                print(f'用 {enc} 编码读取失败: {e}')
        else:
            print('所有编码都无法读取CSV文件，请检查文件格式')
            return
        
        # 导入数据到数据库（有则更新，无则新增）
        for index, row in df.iterrows():
            laptop = Laptop.query.filter_by(original_id=str(row['id'])).first()
            
            # 生成评分
            comment_text = row['comment'] if 'comment' in row and pd.notna(row['comment']) else ""
            rating = generate_rating_from_comment(comment_text)
            
            if laptop:
                # 已存在，更新数据
                laptop.name = row['name']
                laptop.price = float(row['price'])
                laptop.shop = row['shop']
                laptop.brand = row['品牌']
                laptop.ram = row['内存']
                laptop.cpu = row['CPU']
                laptop.sales = int(row['销量'])
                laptop.rating = rating  # 更新评分
                
                # 检查是否有评论数据，如果有且不为空，则添加或更新评论
                if 'comment' in row and pd.notna(row['comment']) and row['comment'].strip():
                    # 检查是否已存在评论
                    existing_comment = Comment.query.filter_by(laptop_id=laptop.id).first()
                    if existing_comment:
                        # 更新现有评论
                        existing_comment.content = row['comment']
                    else:
                        # 添加新评论
                        comment = Comment(content=row['comment'], laptop_id=laptop.id)
                        db.session.add(comment)
            else:
                # 不存在，插入新数据
                laptop = Laptop(
                    original_id=str(row['id']),
                    name=row['name'],
                    price=float(row['price']),
                    shop=row['shop'],
                    brand=row['品牌'],
                    ram=row['内存'],
                    cpu=row['CPU'],
                    sales=int(row['销量']),
                    rating=rating  # 设置评分
                )
                db.session.add(laptop)
                
                # 需要先提交以获取laptop.id
                db.session.flush()
                
                # 添加评论（如果有）
                if 'comment' in row and pd.notna(row['comment']) and row['comment'].strip():
                    comment = Comment(content=row['comment'], laptop_id=laptop.id)
                    db.session.add(comment)
                    
            # 每100条数据提交一次，避免内存占用过大
            if index % 100 == 0:
                db.session.commit()
                print(f'已处理 {index} 条数据')
        # 提交剩余数据
        db.session.commit()
        print(f'数据迁移完成，共处理 {len(df)} 条数据')

if __name__ == '__main__':
    print('开始导入数据...')
    import_csv_to_mysql()
    print('导入完成！')