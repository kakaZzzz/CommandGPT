# Desc: Main entry point for the application
# Auth: kaka
# Date: 2023-6-4
#

# intialize the environment variables
import json
import app.functions as f
import os
import requests
import platform

envs = f.load_env()
os.environ["OPENAI_API_KEY"] = envs["OPENAI_API_KEY"]

os.environ["LANGCHAIN_TRACING"] = "true"

from agents.goal import GoalAgent
from agents.task import TaskAgent

from tools import Tools

tools = Tools()

def run(input_str):

    goal_text = ""
    os_info = platform.system() + " " + platform.release() + " " + platform.machine()

    # Step 1: 基于目标和提示，分析完成目标的步骤（文本形式）
    if input_str.startswith("http"):
        # few shot
        readme = f.getGithubRepo(input_str)
        print( "readme地址:", readme )

        print( "抓取readme..." )
        readme = requests.get(readme)

        print( "GPT分析安装步骤..." )
        goal_text = GoalAgent().run({
                'reference': readme.text,
                'goal': "安装该项目"
            })

        print("\033[93m"+goal_text+"\033[0m")

    else:
        # zero shot
        print( "GPT分析目标..." )
        goal_text = GoalAgent().run({
                'goal': input_str,
                'os_info': os_info
            }) 
        print("\033[93m"+goal_text+"\033[0m")

    # Step 2: 基于步骤文本，整理成json格式
    print( "转换成json..." )
    cmd_json = TaskAgent().run({
        "content": goal_text,
        "os_info": os_info
    })
    print("\033[93m"+cmd_json+"\033[0m")

    # Step 3: json转换成数组，依次执行任务
    cmd = json.loads(cmd_json)
    print(cmd)

    print("开始执行任务：")

    for index, item in enumerate(cmd):
        print("任务", index+1, item)
        
        if item["tool"] == "shell":
            res = tools.run("shell", item["command"])
            print(res)



    