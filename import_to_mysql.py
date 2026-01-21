import pandas as pd
import pymysql
import os
import sys

def import_csv_to_mysql():
    """
    将CSV文件导入到MySQL数据库的jd表中
    """
    # 获取CSV文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'static/data/笔记本电脑_final.csv')
    
    try:
        # 连接到MySQL数据库
        conn = pymysql.connect(
            host='127.0.0.1',  # 使用用户要求的IP
            user='root',       # 使用用户要求的用户名
            password='root',   # 使用用户要求的密码
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 创建数据库（如果不存在）
        cursor.execute("CREATE DATABASE IF NOT EXISTS jd CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE jd")
        
        # 创建jd表（如果不存在）
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS jd (
            id INT AUTO_INCREMENT PRIMARY KEY,
            original_id VARCHAR(255),
            name VARCHAR(500),
            price FLOAT,
            shop VARCHAR(255),
            brand VARCHAR(100),
            ram VARCHAR(50),
            cpu VARCHAR(100),
            sales INT
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """
        cursor.execute(create_table_sql)
        
        # 检查表是否已有数据
        cursor.execute("SELECT COUNT(*) FROM jd")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f'数据库中已有 {count} 条数据，跳过导入')
            conn.close()
            return
        
        # 读取CSV文件
        print(f'正在读取CSV文件: {csv_path}')
        df = pd.read_csv(csv_path, encoding='utf-8')
        print(f'成功读取CSV文件，共 {len(df)} 条数据')
        
        # 准备批量插入数据
        values = []
        for index, row in df.iterrows():
            try:
                values.append((
                    str(row['id']),
                    str(row['name']),
                    float(row['price']),
                    str(row['shop']),
                    str(row['品牌']),
                    str(row['内存']),
                    str(row['CPU']),
                    int(row['销量'])
                ))
                
                # 每500条数据插入一次
                if len(values) >= 500:
                    insert_data(cursor, values)
                    values = []
                    conn.commit()
                    print(f'已导入 {index+1} 条数据')
            except Exception as e:
                print(f'处理第 {index+1} 行数据时出错: {e}')
                continue
        
        # 插入剩余数据
        if values:
            insert_data(cursor, values)
            conn.commit()
        
        print(f'数据导入完成，共导入 {len(df)} 条数据')
        conn.close()
        
    except Exception as e:
        print(f'数据导入失败: {e}')
        if 'conn' in locals() and conn:
            conn.close()

def insert_data(cursor, values):
    """
    批量插入数据到jd表
    """
    insert_sql = """
    INSERT INTO jd (original_id, name, price, shop, brand, ram, cpu, sales)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(insert_sql, values)

if __name__ == "__main__":
    print("开始导入数据到MySQL数据库...")
    import_csv_to_mysql()
    print("导入过程结束")