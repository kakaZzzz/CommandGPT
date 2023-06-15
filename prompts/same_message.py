def system():
    return "你是一个有用的助手，能帮我从一段文字中总结关键词"

def human():
    return """
我的目标是：
\"\"\"{goal}\"\"\"

有可能的答案是：
\"\"\"{answer}\"\"\"

请帮我判断这个答案是否能完成目标，并告诉我原因。

You should only respond in JSON format as described below 
Response Format: 

{{
    "result": "yes or no",
    "reasoning": "reasoning",
}}

Ensure the response can be parsed by Python json.loads

Human: 请告诉结果，并严格按照上述格式返回结果:
"""