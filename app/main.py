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
from agents.next import NextAgent
from agents.keyword import KeywordAgent

from tools import Tools

goal_agent = GoalAgent()
task_agent = TaskAgent()
judge_agent = JudgeAgent()
solution_agent = SolutionAgent()
next_agent = NextAgent()
keyword_agent = KeywordAgent()

tools = Tools()

SOLUTION_RETRY = 3

os_info = platform.system() + " " + platform.release() + " " + platform.machine()

def run(input_str):

    goal_text = ""
    

    # Step 1: 基于目标和提示，分析完成目标的步骤（文本形式）
    if input_str.startswith("http"):
        # few shot
        readme = f.getGithubRepo(input_str)
        f.cyanPrint( "[+]readme地址:", readme )

        f.cyanPrint( "[+]抓取readme..." )
        readme = requests.get(readme)

        f.cyanPrint( "[+]GPT分析安装步骤..." )
        goal_text = GoalAgent().run({
                'reference': readme.text,
                'goal': "安装该项目",
                'os_info': os_info
            })

        print(goal_text)

    else:
        # zero shot
        f.cyanPrint( "[+]GPT分析目标..." )
        goal_text = GoalAgent().run({
                'goal': input_str,
                'os_info': os_info
            }) 
        print(goal_text)

    # Step 2: 基于步骤文本，整理成json格式
    # f.cyanPrint( "[+]转换成json..." )
    # cmd_json = TaskAgent().run({
    #     "content": goal_text,
    #     "os_info": os_info
    # })
    # print(cmd_json)

    f.cyanPrint( "[+]下一步动作..." )
    cmd_json = TaskAgent().run({
        "content": goal_text,
    })
    print(cmd_json)

    # Step 3: json转换成数组，依次执行任务
    cmd = f.json2value(cmd_json)

    for index, item in enumerate(cmd["result"]):
        f.yellowPrint(str(index), "tool: ", item["tool"], " -> command: ", item["command"])
        f.purplePrint ("  reasoning: ", item["reasoning"])
    
    selection = input("请选择执行的任务序号，多个任务用逗号分隔，如1,2,3: ")

    selection_arr = []

    for item in selection.split(","):
        selection_arr.append(cmd["result"][int(item)])

    print(selection_arr)

    f.cyanPrint("[+]开始执行任务：")

    for index, item in enumerate(selection_arr):
        f.cyanPrint("[+]任务", str(index+1), item["tool"])
        
        if item["tool"] == "shell":
            res = tools.run("shell", item["command"])
            print(res)
        elif item["tool"] == "human":
            f.yellowPrint("reasoning: ", item["reasoning"])
            f.yellowPrint("command: ", item["command"])
            f.bluePrint(">>> 请按照提示进行人工操作，执行完毕后按回车键继续")
            continue
        elif item["tool"] == "python_repl":
            res = tools.run("python_repl", item["command"])

        judge_result = judge_agent.run({
            "command": item["command"],
            "info": res
        })

        judge_result = f.json2value(judge_result)
        
        if judge_result["result"] == "success":
            f.greenPrint("[+]任务执行成功: ", judge_result["reasoning"])
        elif judge_result["result"] == "failure":
            f.redPrint("[-]任务执行失败: ", judge_result["reasoning"])

            retry = 0

            while retry < SOLUTION_RETRY:
                f.cyanPrint("[+]尝试解决问题，第", str(retry+1), "次")

                solution_res = solutionTasks(item["tool"], {
                    "command": item["command"],
                    "info": res,
                    "os_info": os_info
                })

                if solution_res:
                    break
        
        f.greenPrint("[+]全部任务执行完成，将该经验存入向量数据库")

        success_dict = {
            "goal": input_str,
            "tasks": selection_arr
        }

        json_text = json.dumps(success_dict, ensure_ascii=False)
        print(json_text)

        keywords = keyword_agent.run({
            "content": json_text
        })

        print(keywords)


def solutionTasks(tool_name, error_obj):
    f.cyanPrint("[+]开始解决问题：")
    f.cyanPrint("[+]工具：", tool_name)

    solution_text = solution_agent.run(error_obj)

    print(solution_text)

    # Step 2: 基于步骤文本，整理成json格式
    f.cyanPrint( "[+]转换成json..." )
    cmd_json = TaskAgent().run({
        "content": solution_text,
        "os_info": os_info
    })
    print(cmd_json)

    cmd = f.json2value(cmd_json)
    print(cmd)

    for index, item in enumerate(cmd["result"]):
        f.yellowPrint(str(index), "tool: ", item["tool"], " -> command: ", item["command"])
        f.purplePrint ("  reasoning: ", item["reasoning"])
    
    selection = input("请选择执行的任务序号，多个任务用逗号分隔，如1,2,3 or 方案不正确输入n: ")

    if selection == "n":
        return False

    selection_arr = []

    for item in selection.split(","):
        selection_arr.append(cmd["result"][int(item)])

    print(selection_arr)

    for index, item in enumerate(cmd["result"]):
        f.cyanPrint("[+]解决问题任务", str(index+1), item["tool"])
        
        if item["tool"] == "shell":
            res = tools.run("shell", item["command"])
            print(res)
        elif item["tool"] == "human":
            f.yellowPrint("reasoning: ", item["reasoning"])
            f.yellowPrint("command: ", item["command"])
            f.bluePrint(">>> 请按照提示进行人工操作，执行完毕后按回车键继续")
            continue
        elif item["tool"] == "python_repl":
            res = tools.run("python_repl", item["command"])

        judge_result = judge_agent.run({
            "command": item["command"],
            "info": res
        })

        judge_result = f.json2value(f.jsonStr(judge_result))
        
        if judge_result["result"] == "success":
            f.greenPrint("[+]任务执行成功: ", judge_result["reasoning"])
        elif judge_result["result"] == "failure":
            f.redPrint("[-]任务执行失败: ", judge_result["reasoning"])
            return False

    f.greenPrint("[+]解决问题任务执行完成")
    return True


    