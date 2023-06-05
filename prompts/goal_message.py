def system():
    return "你是一个专业的程序员，能帮助完成编程相关的事情"

def human_zero_shot():
    return """
目标:
{goal}

你需要在{os_info}环境下完成该目标

Human: 一步一步完成目标，请用markdown文本返回结果，代码要以block方式展示:
"""

def human_few_shot():
    return """
{reference}

基于以上文本，你需要完成以下目标:
{goal}

你需要在{os_info}环境下完成该目标

Human: 一步一步完成目标，请用markdown文本返回结果，代码要以block方式展示:
"""