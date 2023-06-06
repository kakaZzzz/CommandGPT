def system():
    return "你是一个有用的助手，能帮我把理解分析文本"

def human():
    return """
{content}

请理解以上的内容，你只能使用以下3个工具来完成任务：

1. shell. Description: Executes commands in a terminal. Input should be valid commands, and the output will be any output from running that command.需要确保commadn是合法的shell命令，可以在terminal中执行。
2. python_repl. Description: A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.
3. human. 当必须人工操作，或者人工操作更方便和精确时，使用该工具.

请给出执行每个步骤的工具、原因和命令。

You should only respond in JSON format as described below 
Response Format: 
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
Ensure the response can be parsed by Python json.loads
json中的value需要用escape编码

Human: 请告诉转换的结果，并严格按照上述格式返回结果:
"""