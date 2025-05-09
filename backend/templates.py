# backend/templates.py
# 定义可用的 PPT 模板信息

import os

# 获取当前文件（templates.py）所在的目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 模板文件存放的子目录名
TEMPLATES_SUBDIR = "templates"
# 模板文件的完整目录路径
TEMPLATES_DIR = os.path.join(BASE_DIR, TEMPLATES_SUBDIR)

# --- 模板信息列表 ---
# 定义一个列表，每个元素代表一个可用的 PPT 模板
TEMPLATES = [
    {
        "id": "default_simple",
        "name": "Simple & Clean (Default)",
        "path": os.path.join(TEMPLATES_DIR, "simple_template.pptx") # <--- 确保文件名一致
    },
    # --- 新增暗黑科技模板 ---
    {
        "id": "dark_tech", # 新模板的唯一 ID
        "name": "Dark Tech Theme", # 新模板的用户友好名称
        "path": os.path.join(TEMPLATES_DIR, "dark_tech_template.pptx") # <--- **请确保文件名与您创建的模板文件一致**
    },
    # TODO: 如果您创建了更多模板，可以在这里添加
]

# --- 获取模板路径的辅助函数 ---
def get_template_path(template_id: str) -> str | None:
    """
    根据模板 ID 获取模板文件的物理路径。
    """
    for template in TEMPLATES:
        if template["id"] == template_id:
            # 在返回路径之前，再次检查文件是否存在
            if os.path.exists(template["path"]):
                return template["path"]
            else:
                print(f"Warning: Template file not found at path: {template['path']}")
                return None # 文件不存在则返回None
    return None # 没有找到对应的 template_id

# --- 获取模板列表的辅助函数 ---
def get_templates_list() -> list[dict]:
    """
    获取可用模板的列表（不包含物理路径）。
    """
    # 返回时只包含id和name，不暴露内部路径
    return [{"id": t["id"], "name": t["name"]} for t in TEMPLATES]

# --- 初始化检查 (可选) ---
def check_templates_exist():
    """
    检查所有定义的模板文件是否存在。
    """
    print("Checking template files existence...")
    all_exist = True
    for template in TEMPLATES:
        if not os.path.exists(template["path"]):
            print(f"ERROR: Template file NOT FOUND: {template['path']}")
            all_exist = False
        else:
            print(f"Template file found: {template['path']}")
    if all_exist:
        print("All defined template files found.")
    else:
        print("Warning: Some template files are missing!")

# --- 用于本地测试此模块的代码 (可选) ---
if __name__ == "__main__":
    print("Defined Templates:")
    import json
    print(json.dumps(TEMPLATES, indent=2)) # 使用 json 格式化输出
    print("\nTemplate List (for frontend):")
    print(get_templates_list())
    print("\nChecking template paths:")
    check_templates_exist()
    print("\nGetting specific template path (dark_tech):")
    print(get_template_path("dark_tech"))
    print("\nGetting non-existent template path:")
    print(get_template_path("non_existent_template"))