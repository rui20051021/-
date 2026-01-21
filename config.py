# 数据库配置文件
import os
from datetime import timedelta

class Config:
    # 基础配置
    DEBUG = True
    SECRET_KEY = 'laptop_analysis_secret_key'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/jd?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 应用配置
    CSV_FILE_PATH = os.getenv('CSV_FILE_PATH', 'static/data/笔记本电脑_final.csv')
    
    # 登录配置
    REMEMBER_COOKIE_DURATION = timedelta(days=7)  # 记住我的持续时间
    LOGIN_DISABLED = False  # 是否禁用登录功能
    
    # 安全配置
    WTF_CSRF_ENABLED = True  # 启用CSRF保护