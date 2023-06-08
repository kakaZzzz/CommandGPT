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
from agents.summary import SummaryAgent

from tools import Tools
from library import VectorDB
from langchain.schema import Document

goal_agent = GoalAgent()
task_agent = TaskAgent()
judge_agent = JudgeAgent()
solution_agent = SolutionAgent()
next_agent = NextAgent()
keyword_agent = KeywordAgent()
summary_agent = SummaryAgent()

tools = Tools()
db = VectorDB()

SOLUTION_RETRY = 3
SIMILARY_SCORE = 0.1

os_info = platform.system() + " " + platform.release() + " " + platform.machine()

def run(input_str):

    goal_text = ""
    human_goal = ""
    goal_experience = False
    

    # Step 1: 基于目标和提示，分析完成目标的步骤（文本形式）
    if input_str.startswith("http"):
        # few shot
        readme = f.getGithubRepo(input_str)
        f.cyanPrint( "[+]readme地址:", readme )

        f.cyanPrint( "[+]抓取readme..." )
        readme = requests.get(readme)
        print(readme.text)

        f.cyanPrint( "[+]GPT分析安装步骤..." )
        goal_text = GoalAgent(type="few_shot").run({
                'reference': readme.text,
                'goal': "安装该项目",
                'os_info': os_info
            })

        print(goal_text)

        # 从文本中总结出目标
        human_goal = SummaryAgent().run({
            'content': goal_text
        })
        print(human_goal)

    else:
        # zero shot
        f.cyanPrint( "[+]GPT分析目标..." )
        goal_text = GoalAgent().run({
                'goal': input_str,
                'os_info': os_info
            }) 
        
        human_goal = input_str
        print(goal_text)

    search_res = searchExperience("goal: {0}\nos_info: {1}\ntasks:\n{2}".format(input_str, os_info, goal_text))

    if search_res == False:
        # 走全新的流程
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
    else:
        # 找到成功经验的流程
        goal_experience = True
        selection_arr = f.jsonFromFile("library/tasks/" + search_res + ".json")["tasks"]
        print(selection_arr)

    f.cyanPrint("[+]开始执行任务：")

    for index, item in enumerate(selection_arr):
        f.cyanPrint("[+]任务", str(index+1), item["tool"])
        
        res = tools.decompose(item)

        if res == "continue":
            continue

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
        
    if goal_experience == False:

        f.greenPrint("[+]全部任务执行完成，将该经验存入向量数据库")

        success_dict = {
            "goal": human_goal,
            "os_info": os_info,
            "tasks": selection_arr
        }

        storeDB(success_dict)

        


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
        
        res = tools.decompose(item)

        if res == "continue":
            continue

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


def storeDB(success_dict):
    success_text = ""
    for key, value in success_dict.items():
        if key == "tasks":
            success_text += "tasks: \n"
            for index, item in enumerate(value):
                success_text += str(index) + ". tool:" + item["tool"] + "; command:" + item["command"] + "; reasoning:" +item["reasoning"] + ";\n"
        else:
            success_text += key + ": " + value + "\n"
    
    print(success_text)

    json_text = json.dumps(success_dict, ensure_ascii=False)
    print(json_text)

    keywords = keyword_agent.run({
        "content": json_text
    })

    f.greenPrint(keywords)

    # Step 3: 存入数据库
    db.add(success_text, keywords)

    f.json2File(success_dict, "library/tasks/" + keywords + ".json")

def searchExperience(goal_text):
    
    res = db.search(goal_text)

    if len(res) == 0:
        return False
    
    doc, score = res[0]
    print(doc.page_content)
    print(doc.metadata["name"])
    print(score)

    if score < SIMILARY_SCORE:
        return doc.metadata["name"]
    else:
        return False