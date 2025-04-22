# backend/ai_generation.py
# 负责调用外部 AI 模型生成幻灯片数据，并匹配本地图片

import os
from openai import OpenAI
import json
import random # <--- 导入 random 模块用于随机选择图片

# --- DeepSeek API 配置 ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-fO3GLWhzMzngiNrIA06b8078373d44B4Bb03B74535Db4d33") # <--- **请替换为您的实际 DeepSeek API Key**
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://vip.apiyi.com/v1") # <--- **请替换为您的实际 DeepSeek API Base URL**
DEEPSEEK_MODEL_NAME = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-v3-20250324") # <--- **请替换为实际使用的模型名称**

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

# --- 本地图片资源配置与匹配逻辑 ---

# 获取当前文件所在的目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 静态文件目录相对于当前文件的路径
STATIC_DIR_RELATIVE = "static"
# 本地图片文件存放的子目录名
IMAGES_SUBDIR = "images"
# 本地图片文件的完整目录路径
LOCAL_IMAGES_DIR = os.path.join(BASE_DIR, STATIC_DIR_RELATIVE, IMAGES_SUBDIR)

# --- 本地图片关键词映射表 ---
# 定义一个字典，键是图片文件名（相对于 images 目录），值是与图片相关的关键词列表
# 您需要根据您实际放入 backend/static/images 目录的图片来填充这个字典
LOCAL_IMAGE_KEYWORDS_MAP = {
    "tech1.jpg": ["科技", "未来", "数据流", "网络", "code"],
    "city1.jpg": ["城市", "夜景", "建筑", "高楼", "都市"],
    "meeting1.jpg": ["会议", "团队", "合作", "讨论", "商务"],
    "chart1.jpg": ["图表", "数据分析", "增长", "趋势", "统计"],
    "abstract1.jpg": ["抽象", "艺术", "创意", "概念"],
    "health1.jpg": ["健康", "医疗", "研究", "生命科学"], # 示例图片
    "food1.jpg": ["食物", "早餐", "健康饮食", "营养"], # 示例图片
    "space1.jpg": ["太空", "宇宙", "星球", "探索", "火箭"], # 示例图片
    # TODO: 根据您实际添加的图片文件，在这里添加更多的映射关系
}

# --- 简单的本地图片匹配函数 ---
def match_local_image(visual_keywords: list[str] | None) -> str | None:
    """
    根据视觉关键词，在本地图片库中查找最佳匹配的图片。
    返回匹配到的本地图片路径（相对于 STATIC_DIR_RELATIVE 目录），否则返回 None。
    """
    if not visual_keywords:
        return None

    best_match_image = None
    max_score = 0

    # 将输入的关键词转换为小写，方便匹配
    input_keywords_lower = [k.lower() for k in visual_keywords]

    # 遍历本地图片关键词映射表
    for image_file, image_keywords in LOCAL_IMAGE_KEYWORDS_MAP.items():
        # 将图片自身的关键词也转换为小写
        image_keywords_lower = [k.lower() for k in image_keywords]

        # 计算交集得分：输入的关键词和图片关键词有多少重叠
        score = len(set(input_keywords_lower) & set(image_keywords_lower))

        # 如果得分高于当前最高分，更新最佳匹配
        if score > max_score:
            max_score = score
            best_match_image = image_file

    # 可以设置一个最低得分阈值，防止匹配到不相关的图片
    # if max_score == 0:
    #     return None # 如果没有匹配到任何关键词，则不返回图片

    # 返回匹配到的本地图片相对于 STATIC_DIR_RELATIVE 的路径
    if best_match_image:
        return os.path.join(IMAGES_SUBDIR, best_match_image).replace("\\", "/") # 统一使用斜杠作为路径分隔符

    # 如果没有找到匹配的图片，可以随机返回一张图片作为 fallback
    if LOCAL_IMAGE_KEYWORDS_MAP:
         fallback_image = random.choice(list(LOCAL_IMAGE_KEYWORDS_MAP.keys()))
         print(f"Warning: No specific local image matched for keywords {visual_keywords}. Using fallback: {fallback_image}")
         return os.path.join(IMAGES_SUBDIR, fallback_image).replace("\\", "/")


    return None # 如果没有本地图片可用或匹配

# --- Prompt 模板 (保持与之前一致) ---
# 修改 Prompt，增加生成视觉关键词和更丰富的备注的要求
PRESENTATION_PROMPT_TEMPLATE = """
请根据以下内容，生成一个演示文稿（PPT）的大纲、内容和视觉建议。请将演示文稿分为不同的幻灯片，每页幻灯片包含：
1. 一个简洁、吸引人的标题。
2. 3-5个核心要点（使用'- '作为列表符号）。
3. 详细、口语化、包含背景信息和潜在互动点的演讲者备注（在“NOTES:”后面）。
4. 2-3个与本页内容最相关的、可用于查找图片的视觉关键词（在“VISUAL_KEYWORDS:”后面，以逗号分隔）。

请使用以下格式严格输出，每页幻灯片之间用“---”分隔：

幻灯片标题 1
- 要点 1.1
- 要点 1.2
- 要点 1.3
- ...
NOTES: 幻灯片 1 的详细演讲者备注内容，包含更多上下文和讲解提示。
VISUAL_KEYWORDS: 关键词1, 关键词2, 关键词3

---

幻灯片标题 2
- 要点 2.1
- ...
NOTES: 幻灯片 2 的详细演讲者备注内容。
VISUAL_KEYWORDS: 关键词A, 关键词B

---
...以此类推...

请确保生成至少3页幻灯片，内容丰富且有条理。避免生成纯粹的介绍页或目录页作为第一页。内容应基于以下文本：

{input_text}
"""

# --- AI 生成核心函数 ---
def generate_presentation_data(input_text: str):
    """
    调用 AI 模型（DeepSeek API），根据输入文本生成幻灯片数据，并匹配本地图片。
    """
    prompt = PRESENTATION_PROMPT_TEMPLATE.format(input_text=input_text)

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates detailed presentation outlines, speaker notes, and visual suggestions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,
            temperature=0.7,
        )

        ai_output = response.choices[0].message.content.strip()
        print("--- AI Raw Output from DeepSeek ---")
        print(ai_output)
        print("-----------------------------------")

        # --- 解析 AI 的输出 ---
        slides_raw = ai_output.split("---")
        slide_data = []

        for slide_text in slides_raw:
            slide_text = slide_text.strip()
            if not slide_text:
                continue

            lines = slide_text.split('\n')
            title = lines[0].strip() if lines else "Untitled"
            points = []
            notes = ""
            visual_keywords = []

            current_section = "points"

            for line in lines[1:]:
                line = line.strip()
                if not line:
                    if current_section == "notes":
                         notes += "\n"
                    continue

                if line.lower().startswith("notes:"):
                    notes = line[len("NOTES:"):].strip()
                    current_section = "notes"
                elif line.lower().startswith("visual_keywords:"):
                    keywords_str = line[len("VISUAL_KEYWORDS:"):].strip()
                    visual_keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                    current_section = "visual_keywords"
                elif current_section == "points" and line.startswith('- '):
                    points.append(line[2:].strip())
                elif current_section == "notes":
                    notes += "\n" + line
                elif current_section == "visual_keywords":
                     pass # 忽略视觉关键词区域的多余行
                else:
                     if current_section == "notes":
                         notes += "\n" + line
                     elif current_section == "points":
                         points.append(line)


            slide_data.append({
                "title": title,
                "points": points,
                "notes": notes,
                "visual_keywords": visual_keywords
            })

        # 检查并丢弃第一页的介绍性内容
        if slide_data and len(slide_data) > 1:
             first_slide = slide_data[0]
             first_slide_text = (first_slide.get("title", "") + " " + '\n'.join(first_slide.get("points", []))).lower()
             # 增加更多可能的介绍性关键词
             intro_keywords = ["大纲", "目录", "介绍", "引言", "overview", "summary", "contents", "outline"] # <--- 增加英文关键词
             if any(keyword in first_slide_text for keyword in intro_keywords):
                #  print(f"检测到第一页 (ID: {presentation_id if 'presentation_id' in locals() else 'N/A'}) 可能是介绍性内容，正在丢弃。")
                 print("能是介绍性内容，正在丢弃。")
                 slide_data = slide_data[1:]
                 for i, slide_info in enumerate(slide_data):
                      slide_info["order"] = i # 重新设置 order
                 print(f"丢弃介绍页后，剩余 {len(slide_data)} 页。")
             else:
                 print("第一页未检测到介绍性内容，保留。")


        if not slide_data:
            raise ValueError("AI did not generate any usable slides. Please refine input or check AI response.")

        # --- 新增：匹配本地图片并添加到数据结构 ---
        for slide_info in slide_data:
            # 调用本地图片匹配函数
            local_image_relative_path = match_local_image(slide_info.get("visual_keywords"))
            # 将匹配到的本地图片路径添加到 slide_info 中
            slide_info['local_image_path'] = local_image_relative_path # <--- 添加本地图片路径


        return slide_data

    except Exception as e:
        print(f"Error in AI generation or parsing: {e}")
        raise e


# --- 用于本地测试此模块的代码 (可选，可以在此处直接运行测试 AI 调用和图片匹配) ---
if __name__ == "__main__":
    # 在运行前请确保设置了 DEEPSEEK_API_KEY 和 DEEPSEEK_BASE_URL 环境变量
    os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY
    os.environ["DEEPSEEK_BASE_URL"] = DEEPSEEK_BASE_URL
    os.environ["DEEPSEEK_MODEL_NAME"] = DEEPSEEK_MODEL_NAME

    # 确保本地图片目录和一些测试图片存在
    if not os.path.exists(LOCAL_IMAGES_DIR):
         print(f"Creating local images directory: {LOCAL_IMAGES_DIR}")
         os.makedirs(LOCAL_IMAGES_DIR, exist_ok=True)

         # TODO: 如果 LOCAL_IMAGE_KEYWORDS_MAP 不为空，但目录为空，提示用户放入图片

    test_text = """
    人工智能的快速发展带来了巨大的机遇。
    机器学习算法是核心，特别是深度学习。
    AI 在医疗、金融、教育等领域有广泛应用。
    同时，AI 也面临伦理、就业和隐私等挑战。
    未来的AI将更加注重可解释性和安全性。
    国际合作是应对AI挑战的关键。
    """
    print("Running AI generation and local image matching test...")
    try:
       generated_data = generate_presentation_data(test_text)
       import json
       print("--- Parsed Slide Data (with visual keywords and local image path) ---")
       print(json.dumps(generated_data, indent=2, ensure_ascii=False))
       print("-------------------------")
    except Exception as e:
        print(f"AI generation test failed: {e}")