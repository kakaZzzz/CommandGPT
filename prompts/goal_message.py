# !/usr/bin/env python3
"""This module is a template

Author:
Date:
Last modified:
Filename:
"""
def system():
    """

    @return:
    """
    return "你是一个专业的程序员"

# def human_zero_shot():
#     return """
# 目标:
# {goal}

# 你需要在{os_info}环境下完成该目标

# Human: 一步一步完成目标，请用markdown文本返回结果，代码要以block方式展示:
# """

# def human_few_shot():
#     return """
# {reference}

# 你的运行环境是{os_info}

# 请分析理解以上的文本，然后需要完成以下目标:
# {goal}

# Human: 一步一步完成目标，请用markdown文本返回结果，代码要以block方式展示:
# """

def human_zero_shot():
    return """
{{
    "goal": "{goal}",
    "system environment": "{os_info}",
    "constraints": [
        "Lets think step by step",
        "Please use markdown to return the result",
        "Please use block to show the code"
    ],
    "action": "make a todo list"
}} 
"""


def human_few_shot():
    """

    @return:
    """
    return """
{reference}

你的运行环境是{os_info}

请分析理解以上的文本，然后需要完成以下目标:
{goal}

Human: 一步一步完成目标，请用markdown文本返回结果，代码要以block方式展示:
"""