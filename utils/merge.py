import pandas as pd
import os

def merge_same_groups():
    """
    读取合并后的Excel文件，按A列分组，将B、C、D列用顿号合并
    """
    # 输入文件名
    input_file = "合并后的ABCD列数据.xlsx"
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：找不到输入文件 '{input_file}'")
        print("请先运行第一个脚本生成合并数据文件！")
        return
    
    try:
        # 读取Excel文件
        print(f"📖 正在读取文件: {input_file}")
        df = pd.read_excel(input_file, sheet_name='合并数据')
        
        print(f"📊 原始数据: {len(df)} 行")
        
        # 显示原始数据预览
        print(f"\n📋 原始数据预览（前5行）：")
        print(df.head())
        
        # 检查必要的列是否存在
        required_columns = ['A', 'B', 'C', 'D']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"错误：缺少必要的列：{missing_columns}")
            return
        
        # 清理数据：将NaN和空值转换为空字符串
        for col in ['A', 'B', 'C', 'D']:
            df[col] = df[col].fillna('').astype(str).str.strip()
        
        # 删除A列为空的行
        df = df[df['A'] != ''].copy()
        
        if df.empty:
            print("错误：没有有效的数据可以处理（A列全为空）")
            return
        
        print(f"📊 清理后数据: {len(df)} 行")
        
        # 按A列分组并合并B、C、D列
        print(f"\n🔄 开始按A列分组合并...")
        
        def merge_bcd_with_correspondence(group):
            """保持B、C、D列对应关系和统一格式的合并函数"""
            # 获取B、C、D列的原始数据，保持空值
            b_values = []
            c_values = []
            d_values = []
            
            for _, row in group.iterrows():
                b_val = str(row['B']).strip() if str(row['B']).strip() != '' and str(row['B']).strip().lower() != 'nan' else ''
                c_val = str(row['C']).strip() if str(row['C']).strip() != '' and str(row['C']).strip().lower() != 'nan' else ''
                d_val = str(row['D']).strip() if str(row['D']).strip() != '' and str(row['D']).strip().lower() != 'nan' else ''
                
                b_values.append(b_val)
                c_values.append(c_val)
                d_values.append(d_val)
            
            # 确保三列长度一致
            max_length = max(len(b_values), len(c_values), len(d_values))
            
            while len(b_values) < max_length:
                b_values.append('')
            while len(c_values) < max_length:
                c_values.append('')
            while len(d_values) < max_length:
                d_values.append('')
            
            # 创建B、C、D的完整组合列表
            combinations = []
            for i in range(max_length):
                combo = (b_values[i], c_values[i], d_values[i])
                combinations.append(combo)
            
            # 去除重复的组合，保持顺序
            unique_combinations = []
            seen = set()
            for combo in combinations:
                if combo not in seen:
                    unique_combinations.append(combo)
                    seen.add(combo)
            
            # 分离出去重后的B、C、D列，保持空值用'-'表示
            if unique_combinations:
                final_b = []
                final_c = []
                final_d = []
                
                for combo in unique_combinations:
                    # B列：如果为空就用空字符串，否则保持原值
                    final_b.append(combo[0] if combo[0] != '' else '')
                    # C列：如果为空就用空字符串，否则保持原值  
                    final_c.append(combo[1] if combo[1] != '' else '')
                    # D列：如果为空就用'-'，否则保持原值
                    final_d.append(combo[2] if combo[2] != '' else '-')
                
                # 过滤掉全空的组合（B、C、D都为空或"-"）
                filtered_combinations = []
                for i in range(len(final_b)):
                    if final_b[i] != '' or final_c[i] != '' or (final_d[i] != '' and final_d[i] != '-'):
                        filtered_combinations.append((final_b[i], final_c[i], final_d[i]))
                
                if filtered_combinations:
                    final_b = [combo[0] for combo in filtered_combinations]
                    final_c = [combo[1] for combo in filtered_combinations]
                    final_d = [combo[2] for combo in filtered_combinations]
                    
                    return {
                        'B': '、'.join(final_b),
                        'C': '、'.join(final_c),
                        'D': '、'.join(final_d)
                    }
                else:
                    return {'B': '', 'C': '', 'D': ''}
            else:
                return {'B': '', 'C': '', 'D': ''}
        
        # 分组聚合
        grouped_list = []
        for name, group in df.groupby('A'):
            merged_bcd = merge_bcd_with_correspondence(group)
            
            # 合并文件来源
            file_sources = '、'.join(sorted(set(str(val) for val in group['文件来源'] if str(val).strip() != '')))
            
            grouped_list.append({
                'A': name,
                'B': merged_bcd['B'],
                'C': merged_bcd['C'],
                'D': merged_bcd['D'],
                '文件来源': file_sources
            })
        
        grouped_data = pd.DataFrame(grouped_list)
        
        print(f"📊 合并后数据: {len(grouped_data)} 组")
        
        # 显示合并后的数据预览
        print(f"\n📋 合并后数据预览：")
        print(grouped_data.head())
        
        # 输出文件名
        output_file = "按A列分组合并后的数据.xlsx"
        
        # 保存结果到新的Excel文件
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 保存分组合并后的数据
            grouped_data.to_excel(writer, sheet_name='分组合并数据', index=False)
            
            # 同时保存原始数据供参考
            df.to_excel(writer, sheet_name='原始数据', index=False)
        
        print(f"\n✅ 成功！")
        print(f"💾 输出文件：{output_file}")
        print(f"📁 包含两个工作表：")
        print(f"   - '分组合并数据'：按A列分组合并的结果")
        print(f"   - '原始数据'：处理前的原始数据")
        
        # 显示详细统计
        print(f"\n📈 分组统计：")
        
        # 统计每个A列值有多少行原始数据
        original_counts = df['A'].value_counts()
        print(f"📊 原始数据中各A列值的行数分布：")
        for value, count in original_counts.head(10).items():
            # 截断过长的文本用于显示
            display_value = value[:30] + "..." if len(value) > 30 else value
            print(f"  '{display_value}': {count} 行")
        
        if len(original_counts) > 10:
            print(f"  ... 还有 {len(original_counts) - 10} 个分组")
        
        # 显示B、C、D列的合并情况
        print(f"\n📋 合并情况概览：")
        print(f"  B列有内容的分组: {(grouped_data['B'] != '').sum()} / {len(grouped_data)}")
        print(f"  C列有内容的分组: {(grouped_data['C'] != '').sum()} / {len(grouped_data)}")
        print(f"  D列有内容的分组: {(grouped_data['D'] != '').sum()} / {len(grouped_data)}")
        
        # 显示一个具体的合并示例
        if len(grouped_data) > 0:
            example_row = grouped_data.iloc[0]
            print(f"\n📝 合并示例：")
            print(f"  A列: {example_row['A']}")
            print(f"  B列: {example_row['B'][:100]}{'...' if len(str(example_row['B'])) > 100 else ''}")
            print(f"  C列: {example_row['C'][:100]}{'...' if len(str(example_row['C'])) > 100 else ''}")
            print(f"  D列: {example_row['D'][:100]}{'...' if len(str(example_row['D'])) > 100 else ''}")
        
    except Exception as e:
        print(f"✗ 处理过程中发生错误：{e}")
        import traceback
        traceback.print_exc()

def main():
    """
    主函数
    """
    print("🔄 开始按A列分组合并数据...")
    print("-" * 60)
    
    # 检查是否安装了openpyxl
    try:
        import openpyxl
    except ImportError:
        print("⚠️ 缺少依赖库！请先安装：")
        print("pip install openpyxl")
        return
    
    merge_same_groups()
    
    print("-" * 60)
    print("🏁 脚本执行完成！")

if __name__ == "__main__":
    main()