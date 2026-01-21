import pandas as pd
import re
import os

# 读取原始CSV文件
try:
    # 尝试不同的编码方式
    encodings = ['gb18030', 'gbk', 'gb2312', 'utf-8']
    df = None
    
    for encoding in encodings:
        try:
            print(f"尝试使用 {encoding} 编码读取...")
            # 使用正确的文件路径（相对于根目录）
            file_path = '../笔记本电脑_1000items.csv'
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"成功使用 {encoding} 编码读取文件")
            break
        except Exception as e:
            print(f"{encoding} 编码失败: {e}")
    
    if df is None:
        raise Exception("无法读取CSV文件，所有编码尝试均失败")
    
    # 处理商品名称的乱码问题
    def clean_name(name):
        if pd.isna(name):
            return ""
        # 移除不可打印字符
        clean = re.sub(r'[^\x00-\x7F\u4e00-\u9fff]+', '', str(name))
        # 如果清理后为空，尝试保留英文和数字
        if not clean:
            clean = re.sub(r'[^a-zA-Z0-9\s]+', '', str(name))
        return clean.strip()
    
    # 处理shop列的乱码
    def clean_shop(shop):
        if pd.isna(shop):
            return ""
        # 移除不可打印字符
        clean = re.sub(r'[^\x00-\x7F\u4e00-\u9fff]+', '', str(shop))
        return clean.strip()
    
    # 清理name和shop列
    df['name'] = df['name'].apply(clean_name)
    df['shop'] = df['shop'].apply(clean_shop)
    
    # 提取品牌、内存和CPU信息
    common_brands = ['联想', 'lenovo', '华硕', 'asus', '戴尔', 'dell', '惠普', 'hp', '苹果', 'apple', 
                  '华为', 'huawei', '小米', 'xiaomi', '荣耀', 'honor', '宏碁', 'acer', '微星', 'msi', 
                  '机械革命', '神舟', '雷神', '外星人', 'alienware', '三星', 'samsung', 'thinkpad']
    
    # 创建品牌映射
    brand_mapping = {
        'lenovo': '联想', 'asus': '华硕', 'dell': '戴尔', 'hp': '惠普', 'apple': '苹果',
        'huawei': '华为', 'xiaomi': '小米', 'honor': '荣耀', 'acer': '宏碁', 'msi': '微星',
        'alienware': '外星人', 'samsung': '三星', 'thinkpad': '联想'
    }
    
    def extract_brand(name, shop):
        name = str(name).lower()
        shop = str(shop).lower()
        
        # 检查名称中的品牌
        for brand in common_brands:
            if brand.lower() in name:
                # 如果匹配到的是映射表中的英文品牌，返回对应的中文名称
                if brand.lower() in brand_mapping:
                    return brand_mapping[brand.lower()]
                return brand
        
        # 检查店铺名称中的品牌
        for brand in common_brands:
            if brand.lower() in shop:
                if brand.lower() in brand_mapping:
                    return brand_mapping[brand.lower()]
                return brand
        
        return '其他'
    
    # 提取内存信息
    def extract_ram(name):
        name = str(name).lower()
        
        # 尝试匹配常见内存大小模式
        match = re.search(r'(\d+)[g][b]?(?:\s?内存|\s?ram)?', name)
        if match:
            return f"{match.group(1)}GB"
        
        # 尝试匹配其他常见模式
        match = re.search(r'(\d+)\s?[g](?!\w)', name)
        if match:
            return f"{match.group(1)}GB"
        
        # 检查是否包含常见内存大小标示
        for size in ['8g', '16g', '32g', '4g', '64g']:
            if size in name:
                return f"{size[:-1].upper()}GB"
        
        return '8GB'  # 默认值
    
    # 提取CPU信息
    def extract_cpu(name):
        name = str(name).lower()
        
        # Intel 系列
        if 'i3' in name or 'i3-' in name:
            return 'Intel i3'
        elif 'i5' in name or 'i5-' in name:
            return 'Intel i5'
        elif 'i7' in name or 'i7-' in name:
            return 'Intel i7'
        elif 'i9' in name or 'i9-' in name:
            return 'Intel i9'
        
        # AMD 系列
        elif 'ryzen' in name or 'r3' in name or 'r3-' in name:
            return 'Ryzen 3'
        elif 'ryzen' in name or 'r5' in name or 'r5-' in name:
            return 'Ryzen 5'
        elif 'ryzen' in name or 'r7' in name or 'r7-' in name:
            return 'Ryzen 7'
        elif 'ryzen' in name or 'r9' in name or 'r9-' in name:
            return 'Ryzen 9'
        
        # 其他 Intel 处理器
        elif 'intel' in name or 'n4500' in name or 'n100' in name:
            return 'Intel 其他'
        
        # 其他 AMD 处理器
        elif 'amd' in name:
            return 'AMD 其他'
        
        else:
            return '其他'
    
    # 添加提取的列
    df['品牌'] = df.apply(lambda row: extract_brand(row['name'], row['shop']), axis=1)
    df['内存'] = df['name'].apply(extract_ram)
    df['CPU'] = df['name'].apply(extract_cpu)
    
    # 添加销量列（使用id的后三位作为模拟销量）
    df['销量'] = df['id'].apply(lambda x: int(str(x)[-3:]) if pd.notna(x) else 0)
    
    # 保存为新的CSV文件，以UTF-8编码
    new_file_path = os.path.join('static', 'data', '笔记本电脑_processed.csv')
    # 确保目录存在
    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
    df.to_csv(new_file_path, index=False, encoding='utf-8')
    
    print(f"处理完成！新文件已保存为: {new_file_path}")
    
except Exception as e:
    print(f"处理CSV文件时出错: {e}") 