import pandas as pd
import numpy as np
import re
import os
import random
from datetime import datetime

# 设置随机种子以确保结果可重现
random.seed(42)
np.random.seed(42)

# 读取处理过的CSV文件
try:
    print("开始读取数据...")
    file_path = os.path.join('static', 'data', '笔记本电脑_processed.csv')
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"成功读取数据，共 {len(df)} 条记录")
    
    # 1. 保留需要的列，去掉link列和销量列
    if 'link' in df.columns:
        df = df.drop('link', axis=1)
    if '销量' in df.columns:
        df = df.drop('销量', axis=1)
    
    # 2. 生成更真实的销量数据
    print("开始生成更真实的销量数据...")
    
    # 根据品牌和价格区间生成基础销量
    def generate_base_sales(brand, price):
        # 热门品牌基础销量更高
        brand_factor = {
            '联想': 1.3, '华为': 1.4, '小米': 1.2, '苹果': 1.5, '荣耀': 1.2,
            '华硕': 1.0, '戴尔': 1.1, '惠普': 1.0, '外星人': 0.8, '微星': 0.9,
            '宏碁': 0.8, '三星': 0.9, '机械革命': 0.85, '神舟': 0.8, '雷神': 0.8,
            '其他': 0.7
        }
        
        # 价格影响因子：不同价格区间的受欢迎程度
        if price < 4000:
            price_factor = 1.2  # 低价位较受欢迎
        elif 4000 <= price < 6000:
            price_factor = 1.5  # 中低价位最受欢迎
        elif 6000 <= price < 10000:
            price_factor = 1.0  # 中价位一般受欢迎
        else:
            price_factor = 0.7  # 高价位相对小众
        
        # 苹果特殊处理
        if brand == '苹果':
            price_factor = 1.2  # 苹果产品即使价格高也很受欢迎
        
        # 基础销量范围
        base_sales = int(random.normalvariate(500, 150) * (brand_factor.get(brand, 0.7) * price_factor))
        
        # 确保销量在合理范围内
        return max(50, min(base_sales, 5000))
    
    # 根据CPU和内存配置调整销量
    def adjust_sales_by_config(base_sales, cpu, ram):
        # CPU影响系数
        cpu_factor = {
            'Intel i3': 0.8, 'Intel i5': 1.1, 'Intel i7': 1.3, 'Intel i9': 1.4,
            'Ryzen 3': 0.8, 'Ryzen 5': 1.1, 'Ryzen 7': 1.3, 'Ryzen 9': 1.4,
            'Intel 其他': 0.7, 'AMD 其他': 0.7, '其他': 0.6
        }
        
        # 内存影响系数
        ram_size = 8  # 默认8GB
        try:
            ram_size = int(re.search(r'(\d+)', ram).group(1))
        except:
            pass
        
        if ram_size <= 4:
            ram_factor = 0.7
        elif ram_size <= 8:
            ram_factor = 1.0
        elif ram_size <= 16:
            ram_factor = 1.3
        else:
            ram_factor = 1.5
        
        # 调整最终销量
        adjusted_sales = int(base_sales * cpu_factor.get(cpu, 0.8) * ram_factor)
        
        # 添加随机波动（±15%）
        variation = random.uniform(0.85, 1.15)
        
        return int(adjusted_sales * variation)
    
    # 生成销量数据
    df['销量'] = df.apply(
        lambda row: generate_base_sales(row['品牌'], row['price']), axis=1
    )
    
    # 根据配置调整销量
    df['销量'] = df.apply(
        lambda row: adjust_sales_by_config(row['销量'], row['CPU'], row['内存']), axis=1
    )
    
    # 3. 处理价格，确保都是数值型
    df['price'] = df['price'].apply(lambda x: float(str(x).replace(',', '')) if pd.notna(x) else np.nan)
    
    # 4. 调整店铺信息，确保无乱码
    def clean_shop_name(shop):
        if pd.isna(shop) or shop == "":
            return "京东自营"
        if "自营" in shop or "京东" in shop:
            return "京东自营"
        return shop
    
    df['shop'] = df['shop'].apply(clean_shop_name)
    
    # 5. 保存为新的CSV文件
    output_path = os.path.join('static', 'data', '笔记本电脑_improved.csv')
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"处理完成！新文件已保存为: {output_path}")
    print(f"数据统计:")
    print(f"- 记录总数: {len(df)}")
    print(f"- 品牌数量: {df['品牌'].nunique()}")
    print(f"- 平均价格: {df['price'].mean():.2f}")
    print(f"- 平均销量: {df['销量'].mean():.2f}")
    print(f"- 最高销量: {df['销量'].max()}")
    print(f"- 最低销量: {df['销量'].min()}")
    
except Exception as e:
    print(f"处理CSV文件时出错: {e}") 