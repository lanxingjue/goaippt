# backend/ai_generation.py
# 负责调用外部 AI 模型生成幻灯片数据

import os # 导入 os 模块用于读取环境变量
# 导入 openai 库，它兼容 OpenAI 格式的 API，可用于调用 DeepSeek 或其他兼容服务
from openai import OpenAI

# --- DeepSeek API 配置 ---
# 推荐优先从环境变量读取 API Key 和 Base URL，增强安全性
# 如果环境变量未设置，则使用硬编码的 fallback 值 (仅推荐开发测试使用，生产环境严禁硬编码密钥)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-fO3GLWhzMzngiNrIA06b8078373d44B4Bb03B74535Db4d33") # <--- **请替换为您的实际 DeepSeek API Key**
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://vip.apiyi.com/v1") # <--- **请替换为您的实际 DeepSeek API Base URL**
# 您希望使用的 DeepSeek 模型名称
DEEPSEEK_MODEL_NAME = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-v3-20250324") # <--- **请替换为实际使用的模型名称**

# 初始化 OpenAI 客户端，配置为连接到 DeepSeek API
client = OpenAI(
    api_key=DEEPSEEK_API_KEY, # 使用 DeepSeek API Key
    base_url=DEEPSEEK_BASE_URL # 使用 DeepSeek API Base URL
)

# --- Prompt 模板 ---
# 用于指导 AI 模型生成幻灯片大纲和内容
PRESENTATION_PROMPT_TEMPLATE = """
请根据以下内容，生成一个演示文稿（PPT）的大纲和内容。请将演示文稿分为不同的幻灯片，每页幻灯片包含：
1. 一个简洁的标题。
2. 几个核心要点（使用'- '作为列表符号）。
3. 详细的演讲者备注（在“NOTES:”后面）。

请使用以下格式严格输出，每页幻灯片之间用“---”分隔：

幻灯片标题 1
- 要点 1.1
- 要点 1.2
- 要点 1.3
NOTES: 幻灯片 1 的详细演讲者备注内容。

---

幻灯片标题 2
- 要点 2.1
- 要点 2.2
NOTES: 幻灯片 2 的详细演讲者备注内容。

---
...以此类推...

请确保生成至少3页幻灯片，内容丰富且有条理。内容应基于以下文本：

{input_text}
"""

# --- AI 生成核心函数 ---
def generate_presentation_data(input_text: str):
    """
    调用 AI 模型（DeepSeek API），根据输入文本生成幻灯片数据。
    """
    # 格式化 Prompt 模板，将用户输入文本填充进去
    prompt = PRESENTATION_PROMPT_TEMPLATE.format(input_text=input_text)

    try:
        # 调用 chat completions API 生成文本
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL_NAME, # 使用配置的模型名称
            messages=[
                # 系统消息，设定 AI 的角色和行为
                {"role": "system", "content": "You are a helpful assistant that creates presentation outlines and speaker notes."},
                # 用户消息，提供输入文本和生成指令
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000, # 设置最大生成 token 数，根据内容复杂度和页数调整
            temperature=0.7, # 控制生成结果的创造性，0表示确定性高，1表示随机性高
            # top_p=1, # 可选参数，控制生成结果的多样性
            # frequency_penalty=0, # 可选参数，控制重复度
            # presence_penalty=0, # 可选参数，控制新主题的引入
        )

        # 提取 AI 生成的文本内容
        ai_output = response.choices[0].message.content.strip()
        print("--- AI Raw Output from DeepSeek ---")
        print(ai_output)
        print("-----------------------------------")


        # --- 解析 AI 的输出 ---
        # 将 AI 生成的文本解析成结构化的幻灯片数据列表
        slides_raw = ai_output.split("---") # 按分隔符分割每页幻灯片内容
        slide_data = []

        for slide_text in slides_raw:
            slide_text = slide_text.strip()
            if not slide_text:
                continue # 跳过空段落

            lines = slide_text.split('\n')
            # 第一行通常是标题
            title = lines[0].strip() if lines else "Untitled"
            points = [] # 用于存储要点
            notes = "" # 用于存储备注
            notes_started = False # 标记是否已进入备注区域

            # 遍历剩余行，解析要点和备注
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue # 跳过空行

                # 检查是否是备注行的开头（不区分大小写）
                if line.lower().startswith("notes:"):
                    notes = line[len("NOTES:"):].strip() # 提取“NOTES:”后面的内容作为备注开头
                    notes_started = True # 标记备注已开始
                # 如果已经进入备注区域，则后续非空行都添加到备注中（保留换行）
                elif notes_started:
                    notes += "\n" + line
                # 如果还没进入备注区域，且是以 '- ' 开头，则认为是要点
                elif line.startswith('- '):
                    points.append(line[2:].strip()) # 提取 '- ' 后面的内容作为要点
                # 如果既不是备注开头，也不是要点行，且备注还没开始，先当作要点处理 (MVP简化处理)
                else:
                     if notes_started:
                         notes += "\n" + line # 如果备注已开始，也添加到备注
                     else:
                         points.append(line) # 否则添加到要点


            # 将解析出的数据添加到幻灯片数据列表中
            slide_data.append({
                "title": title,
                "points": points,
                "notes": notes
            })

        # 如果 AI 没有生成任何幻灯片，可以返回一个错误或默认页
        if not slide_data:
            raise ValueError("AI did not generate any slides. Please check the input text or AI response.")


        return slide_data

    except Exception as e:
        # 捕获调用 API 或解析过程中发生的异常
        print(f"Error in AI generation: {e}")
        # 重新抛出异常，让调用方（main.py）处理
        raise e


# --- 用于本地测试此模块的代码 (可选，可以在此处直接运行测试 AI 调用) ---
if __name__ == "__main__":
    # 在运行前请确保设置了 DEEPSEEK_API_KEY 和 DEEPSEEK_BASE_URL 环境变量
    test_text = """
    太空探索的未来充满挑战和机遇。
    未来的太空探索目标包括重返月球、载人登陆火星，以及探索太阳系外的宜居行星。
    技术发展是关键，包括更高效的推进系统、更先进的生命支持系统和更强的通信技术。
    私营航天公司如 SpaceX 和 Blue Origin 正在发挥越来越重要的作用，降低了进入太空的成本。
    国际合作对于大型项目至关重要，如国际空间站（ISS）和未来的月球基地计划。
    太空探索不仅推动科技进步，也激发人类好奇心，拓展我们对宇宙的认知。
    同时，也面临成本巨大、风险高、太空垃圾等挑战。
    伦理问题，如地外生命接触和太空资源利用，也需要被认真考虑。
    """
    print("Running AI generation test with DeepSeek...")
    try:
       generated_data = generate_presentation_data(test_text)
       import json
       print("--- Parsed Slide Data ---")
       print(json.dumps(generated_data, indent=2, ensure_ascii=False))
       print("-------------------------")
    except Exception as e:
        print(f"AI generation test failed: {e}")