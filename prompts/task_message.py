def system():
    return "你是一个有用的助手，能帮我把理解分析文本"

def human():
    return """
{content}

请充分分析和理解以上的内容

{tools}

请给出执行每个步骤的工具、原因和命令。

You should only respond in JSON format as described below 
Response Format: 
{{
    "result": 
    [
        {{
        "tool": "tool name",
        "reasoning": "thought",
        "command": "command"
        }},
        {{
        "tool": "tool name",
        "reasoning": "thought",
        "command": "command"
        }},
        {{
        "tool": "tool name",
        "reasoning": "thought",
        "command": "command"
        }},
    ]
}}

command中如果包含&&、;、"或"这三个符号，必须要拆成多条command
Ensure the response can be parsed by Python json.loads
json中的value需要用escape编码

Human: 请告诉转换的结果，并严格按照上述格式返回结果:
"""