import os
directories_all = []
def find_directories_with_bc(start_path):
    """
    遍历指定路径下的所有子目录，检查哪些目录（及其子目录）中包含以 .bc 结尾的文件。

    Args:
    start_path (str): 要遍历的根目录路径

    Returns:
    list: 包含 .bc 文件的子目录名称列表
    """
    directories_with_bc = []
    
    # 遍历 start_path 下的每个直接子目录
    for subdir in next(os.walk(start_path))[1]:
        directories_all.append(subdir)
        full_subdir_path = os.path.join(start_path, subdir)
        for dirpath, dirnames, filenames in os.walk(full_subdir_path):
            for filename in filenames:
                if filename.endswith('.bc'):
                    if subdir not in directories_with_bc:
                        directories_with_bc.append(subdir)
                    # 一旦找到.bc文件，跳出当前循环
                    break
            else:
                # 继续外层循环，如果内层循环未break（即未找到.bc文件）
                continue
            # 内层循环找到.bc文件后执行break，这里break外层循环
            break
        

    return directories_with_bc

def find_directories_with_source(start_path):
    """
    遍历指定路径下的所有子目录，检查哪些目录（及其子目录）中包含以 .bc 结尾的文件。

    Args:
    start_path (str): 要遍历的根目录路径

    Returns:
    list: 包含 .bc 文件的子目录名称列表
    """
    directories_with_bc = []
    
    # 遍历 start_path 下的每个直接子目录
    for subdir in next(os.walk(start_path))[1]:
        full_subdir_path = os.path.join(start_path, subdir)
        for dirpath, dirnames, filenames in os.walk(full_subdir_path):
            for filename in filenames:
                if filename.endswith('.bc'):
                    if subdir not in directories_with_bc:
                        directories_with_bc.append(subdir)
                    # 一旦找到.bc文件，跳出当前循环
                    break
            else:
                # 继续外层循环，如果内层循环未break（即未找到.bc文件）
                continue
            # 内层循环找到.bc文件后执行break，这里break外层循环
            break
        

    return directories_with_bc

# 使用示例
if __name__ == "__main__":
    start_path = '/p/lustre3/shan4/database/corpus'  # 设置要遍历的起始目录
    directories = find_directories_with_bc(start_path)
    directories1 = find_directories_with_source(start_path)    
    # 打印结果
    # if directories:
    #     print("Subdirectories containing '.bc' files:")
    #     for directory in directories:
    #         print(directory)
    # else:
    #     print("No subdirectories with '.bc' files found.")
        
    
    # if directories1:
    #     print("Subdirectories containing '.bc' files:")
    #     for directory in directories1:
    #         print(directory)
    # else:
    #     print("No subdirectories with '.bc' files found.")
    print("Subdirectories without '.bc' files:")
    for dic in directories_all:
        if dic not in directories and dic not in directories1:
            print(dic)
