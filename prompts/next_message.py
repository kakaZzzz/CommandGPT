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
    return "你是一个有用的助手，能帮助我决策下一步该做什么"


def human():
    """

    @return:
    """
    return """
任务执行步骤是：
{steps}

你可以参考的之前执行的信息是：
{done}

请理解以上的内容，你只能使用以下4个工具来完成任务：
1. shell. Description: Executes commands in a terminal. Input should be valid commands, and the output will be any output from running that command.需要确保commadn是合法的shell命令，可以在terminal中执行。
2. python_repl. Description: A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.
3. human. 当必须人工操作，或者人工操作更方便和精确时，使用该工具.
4. finish. Description: This is a special tool that you can use to indicate that you have finished the task. You should not use this tool unless you have completed the task.

我的目标是：
{goal}

基于以上信息，请告诉我下一步该做什么？

You should only respond in JSON format as described below 
Response Format: 

{{
    "tool": "tool name",
    "reasoning": "reasoning",
    "command": "command"
}}


Ensure the response can be parsed by Python json.loads

Human: 请告诉结果，并严格按照上述格式返回结果:
"""