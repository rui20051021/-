import pandas as pd
import re
import os

# 读取改进后的CSV文件
try:
    print("开始读取数据...")
    file_path = os.path.join('static', 'data', '笔记本电脑_improved.csv')
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"成功读取数据，共 {len(df)} 条记录")
    
    # 统计分析
    print(f"当前品牌分布:")
    print(df['品牌'].value_counts())
    print(f"\n当前CPU分布:")
    print(df['CPU'].value_counts())
    
    # 1. 从shop列进一步识别品牌
    print("\n开始从shop列识别更多品牌...")
    
    # 创建品牌关键词映射
    shop_brand_keywords = {
        '联想': ['联想', 'lenovo', 'thinkpad', '拯救者', '小新'],
        '华硕': ['华硕', 'asus', '玩家国度', 'rog'],
        '戴尔': ['戴尔', 'dell', 'alienware', '外星人'],
        '惠普': ['惠普', 'hp', '光影精灵'],
        '苹果': ['苹果', 'apple', 'mac', '蘋果'],
        '华为': ['华为', 'huawei', 'matebook'],
        '小米': ['小米', 'xiaomi', 'redmi'],
        '荣耀': ['荣耀', 'honor', 'magicbook'],
        '宏碁': ['宏碁', 'acer', '暗影骑士', '掠夺者', 'predator'],
        '微星': ['微星', 'msi'],
        '机械革命': ['机械革命'],
        '神舟': ['神舟', 'hasee'],
        '雷神': ['雷神'],
        '三星': ['三星', 'samsung'],
        '技嘉': ['技嘉', 'gigabyte', 'aorus'],
        '七彩虹': ['七彩虹', 'colorful'],
        '海尔': ['海尔'],
        '清华同方': ['清华同方', 'thtf'],
        '万耀': ['万耀'],
        '炫龙': ['炫龙'],
        '火影': ['火影'],
        'lg': ['lg']
    }
    
    # 从shop列识别品牌
    def identify_brand_from_shop(row):
        if row['品牌'] != '其他':
            return row['品牌']
        
        shop = str(row['shop']).lower()
        name = str(row['name']).lower()
        
        for brand, keywords in shop_brand_keywords.items():
            for keyword in keywords:
                if keyword.lower() in shop or keyword.lower() in name:
                    return brand
        
        return '其他'
    
    # 应用品牌识别
    df['品牌'] = df.apply(identify_brand_from_shop, axis=1)
    
    # 2. 从name列进一步识别CPU
    print("\n开始从name列识别更多CPU型号...")
    
    # CPU关键词映射
    cpu_keywords = {
        'Intel i3': ['i3-', ' i3 ', 'core i3', '酷睿i3'],
        'Intel i5': ['i5-', ' i5 ', 'core i5', '酷睿i5'],
        'Intel i7': ['i7-', ' i7 ', 'core i7', '酷睿i7'],
        'Intel i9': ['i9-', ' i9 ', 'core i9', '酷睿i9'],
        'Ryzen 3': ['ryzen 3', 'r3-', ' r3 ', 'amd r3'],
        'Ryzen 5': ['ryzen 5', 'r5-', ' r5 ', 'amd r5'],
        'Ryzen 7': ['ryzen 7', 'r7-', ' r7 ', 'amd r7'],
        'Ryzen 9': ['ryzen 9', 'r9-', ' r9 ', 'amd r9'],
        'Intel 奔腾': ['pentium', '奔腾'],
        'Intel 赛扬': ['celeron', '赛扬'],
        'Intel 至强': ['xeon', '至强'],
        'AMD 锐龙': ['ryzen', '锐龙'],
        'AMD 速龙': ['athlon', '速龙'],
        'M1': ['m1', 'm1芯片'],
        'M2': ['m2', 'm2芯片'],
        'M3': ['m3', 'm3芯片'],
        'Intel N系列': ['n100', 'n305', 'n95', 'n4500', 'n4505', 'n5100', 'n5105'],
        'Intel J系列': ['j4125', 'j3455', 'j4105']
    }
    
    # 从name列识别CPU
    def identify_cpu_from_name(row):
        if row['CPU'] != '其他':
            return row['CPU']
        
        name = str(row['name']).lower()
        
        for cpu_type, keywords in cpu_keywords.items():
            for keyword in keywords:
                if keyword.lower() in name:
                    return cpu_type
        
        # 特殊情况处理
        if '酷睿' in name or 'core' in name:
            return 'Intel 其他'
        if 'amd' in name:
            return 'AMD 其他'
        
        return '其他'
    
    # 应用CPU识别
    df['CPU'] = df.apply(identify_cpu_from_name, axis=1)
    
    # 3. 保存为最终版CSV文件
    output_path = os.path.join('static', 'data', '笔记本电脑_final.csv')
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    # 显示结果
    print("\n数据精细化处理完成！")
    print(f"处理后品牌分布:")
    print(df['品牌'].value_counts())
    print(f"\n处理后CPU分布:")
    print(df['CPU'].value_counts())
    print(f"\n新文件已保存为: {output_path}")
    
except Exception as e:
    print(f"处理CSV文件时出错: {e}") 