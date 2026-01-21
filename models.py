# 数据库模型定义
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Laptop(db.Model):
    __tablename__ = 'jd'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    original_id = db.Column(db.String(20))  # 原始CSV中的ID
    name = db.Column(db.String(255))  # 笔记本名称
    price = db.Column(db.Float)  # 价格
    shop = db.Column(db.String(100))  # 店铺
    brand = db.Column(db.String(50))  # 品牌
    ram = db.Column(db.String(20))  # 内存
    cpu = db.Column(db.String(50))  # CPU
    sales = db.Column(db.Integer)  # 销量
    rating = db.Column(db.Float, default=0.0)  # 新增：评分字段
    ram_gb = db.Column(db.Integer, index=True)
    __table_args__ = (
        db.Index('ix_jd_brand_ram', 'brand', 'ram'),
        db.Index('ix_jd_brand_cpu', 'brand', 'cpu'),
    )
    
    # 建立与评论的一对多关系
    comments = db.relationship('Comment', backref='laptop', lazy='dynamic')
    
    def __repr__(self):
        return f'<Laptop {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'original_id': self.original_id,
            'name': self.name,
            'price': self.price,
            'shop': self.shop,
            'brand': self.brand,
            'ram': self.ram,
            'cpu': self.cpu,
            'sales': self.sales,
            'rating': self.rating
        }

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text)  # 评论内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 评论时间
    laptop_id = db.Column(db.Integer, db.ForeignKey('jd.id'))  # 外键关联到笔记本
    
    def __repr__(self):
        return f'<Comment {self.id} for Laptop {self.laptop_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at,
            'laptop_id': self.laptop_id
        }