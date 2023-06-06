def system():
    return "你是一个有用的助手，能帮我判断命令是否执行成功"

def human():
    return """
执行的命令是：
{command}

{info}

You should only respond in JSON format as described below 
Response Format: 
{{
    "result": "success or failure",
    "reasoning": "reasoning for success or failure"
}}
Ensure the response can be parsed by Python json.loads

请根据以上信息，分析命令是否执行成功，严格按照上述json格式返回结果，原因写在reasoning中，不用返回额外的文本:
"""