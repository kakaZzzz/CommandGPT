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
from agents.judge import JudgeAgent
from agents.solution import SolutionAgent

from tools import Tools

goal_agent = GoalAgent()
task_agent = TaskAgent()
judge_agent = JudgeAgent()
solution_agent = SolutionAgent()
tools = Tools()

SOLUTION_RETRY = 3

os_info = platform.system() + " " + platform.release() + " " + platform.machine()

def run(input_str):

    goal_text = ""
    

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
                'goal': "安装该项目",
                'os_info': os_info
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
        elif item["tool"] == "human":
            print("reasoning: ", item["reasoning"])
            print("command: ", item["command"])
            input("请按照提示进行人工操作，执行完毕后按回车键继续")
            continue
        elif item["tool"] == "python_repl":
            res = tools.run("python_repl", item["command"])

        judge_result = judge_agent.run({
            "command": item["command"],
            "info": res
        })

        judge_result = json.loads(f.jsonStr(judge_result))
        
        if judge_result["result"] == "success":
            print("\033[92m"+judge_result["reasoning"]+"\033[0m")
        elif judge_result["result"] == "failure":
            print("\033[91m"+judge_result["reasoning"]+"\033[0m")

            retry = 0

            while retry < SOLUTION_RETRY:
                print("尝试解决问题，第", retry+1, "次")

                solution_res = solutionTasks(item["tool"], {
                    "command": item["command"],
                    "info": res,
                    "os_info": os_info
                })

                if solution_res:
                    break


def solutionTasks(tool_name, error_obj):
    print("开始解决问题：")
    print("工具：", tool_name)
    print("错误信息：", error_obj)

    solution_text = solution_agent.run(error_obj)

    print("\033[93m"+solution_text+"\033[0m")

    # Step 2: 基于步骤文本，整理成json格式
    print( "转换成json..." )
    cmd_json = TaskAgent().run({
        "content": solution_text,
        "os_info": os_info
    })
    print("\033[93m"+cmd_json+"\033[0m")

    cmd = json.loads(cmd_json)
    print(cmd)

    for index, item in enumerate(cmd):
        print("解决问题任务", index+1, item)
        
        if item["tool"] == "shell":
            res = tools.run("shell", item["command"])
            print(res)
        elif item["tool"] == "human":
            print("reasoning: ", item["reasoning"])
            print("command: ", item["command"])
            input("请按照提示进行人工操作，执行完毕后按回车键继续")
            continue
        elif item["tool"] == "python_repl":
            res = tools.run("python_repl", item["command"])

        judge_result = judge_agent.run({
            "command": item["command"],
            "info": res["info"]
        })

        judge_result = json.loads(f.jsonStr(judge_result))
        
        if judge_result["result"] == "success":
            print("\033[92m"+judge_result["reasoning"]+"\033[0m")
        elif judge_result["result"] == "failure":
            print("\033[91m解法失败\033[0m")
            return False

    print("\033[92m解法任务执行完成\033[0m")
    return True


    