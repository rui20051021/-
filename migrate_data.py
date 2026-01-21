# 数据迁移脚本 - 将CSV数据导入到MySQL数据库
import os
import pandas as pd
from flask import Flask
from models import db, Laptop
from config import Config
import re

# 创建应用实例
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

def migrate_csv_to_mysql(csv_path=None):
    """
    将CSV数据迁移到MySQL数据库
    :param csv_path: 可选的自定义CSV文件路径
    """
    with app.app_context():
        # 创建数据库表
        db.create_all()
        
        # 获取CSV文件路径
        if not csv_path:
            csv_path = Config.CSV_FILE_PATH if os.path.isabs(Config.CSV_FILE_PATH) else os.path.join(app.root_path, Config.CSV_FILE_PATH)
        
        try:
            # 读取CSV文件
            print(f'正在读取CSV文件: {csv_path}')
            df = pd.read_csv(csv_path, encoding='utf-8')
            print(f'成功读取CSV文件，共 {len(df)} 条数据')
            
            # 统计更新和新增的数量
            updated_count = 0
            added_count = 0
            
            # 处理每行数据
            for index, row in df.iterrows():
                try:
                    # 检查是否已存在相同original_id的记录
                    existing = Laptop.query.filter_by(original_id=str(row['id'])).first()
                    
                    if existing:
                        # 更新现有记录
                        existing.name = row['name']
                        existing.price = float(row['price'])
                        existing.shop = row['shop']
                        existing.brand = row['品牌']
                        existing.ram = row['内存']
                        existing.cpu = row['CPU']
                        existing.sales = int(row['销量'])
                        updated_count += 1
                    else:
                        # 添加新记录
                        laptop = Laptop(
                            original_id=str(row['id']),
                            name=row['name'],
                            price=float(row['price']),
                            shop=row['shop'],
                            brand=row['品牌'],
                            ram=row['内存'],
                            cpu=row['CPU'],
                            sales=int(row['销量'])
                        )
                        db.session.add(laptop)
                        added_count += 1
                    
                    # 每500条数据提交一次
                    if index % 500 == 0:
                        db.session.commit()
                        print(f'已处理 {index+1} 条数据 (新增: {added_count}, 更新: {updated_count})')
                
                except Exception as e:
                    print(f'处理第 {index+1} 行数据时出错: {e}')
                    continue
            
            # 提交剩余数据
            db.session.commit()
            print(f'数据处理完成! 共处理 {len(df)} 条数据 (新增: {added_count}, 更新: {updated_count})')
            
        except Exception as e:
            db.session.rollback()
            print(f'数据迁移失败: {e}')
            raise

if __name__ == '__main__':
    migrate_csv_to_mysql()
    
def parse_ram_gb(text):
    if not isinstance(text, str):
        return None
    m = re.search(r'(\d{1,3})\s*(?:GB|G|gb|g)', text)
    if not m:
        return None
    try:
        v = int(m.group(1))
        if v <= 0 or v > 1024:
            return None
        return v
    except Exception:
        return None

def backfill_ram_gb(batch_size=500):
    with app.app_context():
        exists = db.session.execute(db.text("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name='jd' AND column_name='ram_gb'")).scalar()
        if not exists:
            db.session.execute(db.text('ALTER TABLE jd ADD COLUMN ram_gb INT NULL'))
            db.session.commit()
        q = db.session.query(Laptop).filter((Laptop.ram_gb.is_(None)) | (Laptop.ram_gb == 0))
        idx = 0
        for laptop in q.yield_per(batch_size):
            v = parse_ram_gb(laptop.ram)
            laptop.ram_gb = v if v is not None else None
            idx += 1
            if idx % batch_size == 0:
                db.session.commit()
        db.session.commit()