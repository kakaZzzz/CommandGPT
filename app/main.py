# !/usr/bin/env python3
# Desc: Main entry point for the application
# Auth: kaka
# Date: 2023-6-4
#

# intialize the environment variables

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from redis import Redis
from starlette_session import SessionMiddleware
from starlette_session.backends import BackendType


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
from agents.fix import FixAgent
from agents.next import NextAgent
from agents.keyword import KeywordAgent
from agents.summary import SummaryAgent
from agents.same import SameAgent

from tools import Tools
from library import VectorDB
from langchain.schema import Document

goal_agent = GoalAgent()
task_agent = TaskAgent()
judge_agent = JudgeAgent()
fix_agent = FixAgent()
next_agent = NextAgent()
keyword_agent = KeywordAgent()
summary_agent = SummaryAgent()
same_agent = SameAgent()

tools = Tools()
db = VectorDB()

ERROR_FIX_RETRY = 3          # 纠错重试次数
SIMILARY_SCORE = 0.1        # 向量搜索相似度阈值，小于该值则认为是相同的，直接返回
CHECK_SCORE = 0.3           # 需要AI判断的相似度阈值，小于该值则认为是相似但不确定的，需要AI判断

G = {
    "final_goal": "",
    "task_text": "",
    "finded_experience": False,
    "os_info": platform.system() + " " + platform.release() + " " + platform.machine(),
    "api":False
}


def runTask(arr, type="goal"):

    prefix = ""
    if type == "fix":
        prefix = "[+]ErrorFix任务"
    else:
        prefix = "[+]任务"

    for index, item in enumerate(arr):
        f.cyanPrint(prefix, str(index+1), item["tool"])
        
        res = tools.decompose(item)

        if res == "continue":
            continue

        judge_result = judge_agent.run({
            "command": item["command"],
            "info": res
        })

        judge_result = f.json2value(judge_result)
        
        if judge_result["result"] == "success":
            f.greenPrint(prefix+"执行成功: ", judge_result["reasoning"])
        elif judge_result["result"] == "failure":
            f.redPrint(prefix+"执行失败: ", judge_result["reasoning"])

            if type == "goal":
                # 目标任务执行失败，尝试ErrorFix
                retry = 0

                while retry < ERROR_FIX_RETRY:
                    retry += 1
                    f.cyanPrint("[+]尝试ErrorFix，第", str(retry), "次")

                    fix_res = errorFix(item["tool"], {
                        "command": item["command"],
                        "info": res,
                        "os_info": G["os_info"]
                    })

                    if fix_res:
                        break
                    else:
                        f.redPrint("[-]ErrorFix失败")

                if retry == ERROR_FIX_RETRY:
                    f.redPrint("[-]ErrorFix超次数，需要人工介入")
                    input("请人工介入，ErrorFix后按回车继续...")
                    return False

            elif type == "fix":
                return False
    
    # 任务全部执行完成，代表成功
    return True

        
def fewShotGoalByUrl(url):
    # few shot
    readme = f.getGithubRepo(url)
    f.cyanPrint( "[+]readme地址:", readme )

    f.cyanPrint( "[+]抓取readme..." )
    readme = requests.get(readme)
    print(readme.text)

    f.cyanPrint( "[+]GPT分析安装步骤..." )
    G["task_text"] = GoalAgent(type="few_shot").run({
            'reference': readme.text,
            'goal': "安装该项目",
            'os_info': G["os_info"]
        })

    print(G["task_text"])

    # 从文本中总结出目标
    G["final_goal"] = SummaryAgent().run({
        'content': G["task_text"]
    })
    print(G["final_goal"])
    return G["final_goal"]


def zeroShotGoal(goal):
    # zero shot
    f.cyanPrint( "[+]GPT分析目标..." )
    G["task_text"] = GoalAgent().run({
            'goal': goal,
            'os_info': G["os_info"]
        }) 
    
    G["final_goal"] = goal
    print(G["task_text"])
    return G["task_text"]


def newTask():
    # 走全新的流程
    f.cyanPrint( "[+]下一步动作..." )
    cmd_json = TaskAgent().run({
        "content": G["task_text"],
    })
    print(cmd_json)

    # Step 3: json转换成数组，依次执行任务
    cmd = f.json2value(cmd_json)

    for index, item in enumerate(cmd["result"]):
        f.yellowPrint(str(index), "tool: ", item["tool"], " -> command: ", item["command"])
        f.purplePrint ("  reasoning: ", item["reasoning"])

    if G["api"]:
        return cmd["result"]
    
    selection = input("请选择执行的任务序号，多个任务用逗号分隔，如1,2,3: ")

    selection_arr = []

    for item in selection.split(","):
        selection_arr.append(cmd["result"][int(item)])

    print(selection_arr)

    return selection_arr


def errorFix(tool_name, error_obj):
    f.cyanPrint("[+]开始ErrorFix：")
    f.cyanPrint("[+]工具：", tool_name)

    solution_text = fix_agent.run(error_obj)

    print(solution_text)

    # Step 2: 基于步骤文本，整理成json格式
    f.cyanPrint( "[+]转换成json..." )
    cmd_json = TaskAgent().run({
        "content": solution_text,
        "os_info": G["os_info"]
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

    fix_res = runTask(selection_arr, type="fix")

    if fix_res == False:
        return False
    else:
        f.greenPrint("[+]ErrorFix任务执行完成")
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


def searchExperience(goal_and_os):
    
    res = db.search(goal_and_os)

    if len(res) == 0:
        return False
    
    doc, score = res[0]
    print(doc.page_content)
    print(doc.metadata["name"])
    print(score)

    if score < SIMILARY_SCORE:
        return doc.metadata["name"]
    elif score < CHECK_SCORE:
        same_res = same_agent.run({
            "goal": goal_and_os,
            "answer": doc.page_content
        })
        
        same_dict = f.json2value(same_res)

        if same_dict["result"] == "yes":
            f.greenPrint("[+]找到相似经验：", same_dict["reasoning"])
            return doc.metadata["name"]
        else:
            f.redPrint("[-]未找到相似经验: ", same_dict["reasoning"])
            return False
        
    else:
        return False
    

# Command Line

def run(input_str):

    # Step 1: 基于目标和提示，分析完成目标的步骤（文本形式）
    if input_str.startswith("http"):
        fewShotGoalByUrl(input_str)
    else:
        zeroShotGoal(input_str)

    # Step 2: 查询是否有相同的经验可以复用
    search_res = searchExperience("goal: {0}\nos_info: {1}".format(G["final_goal"], G["os_info"]))

    if search_res == False:
        # Step 2.1: 没有相同的经验，开始AI分解新任务
        selection_arr = newTask()
    else:
        # Step 2.2: 有相同的经验，直接执行
        G["finded_experience"] = True
        selection_arr = f.jsonFromFile("library/tasks/" + search_res + ".json")["tasks"]
        print(selection_arr)

    # Step 3: 执行任务
    f.cyanPrint("[+]开始执行任务：")
    runTask(selection_arr)
    
    # Step 4: 任务执行完成，存入向量数据库
    if G["finded_experience"] == False:

        f.greenPrint("[+]全部任务执行完成，将该经验存入向量数据库")

        success_dict = {
            "goal": G["final_goal"],
            "os_info": G["os_info"],
            "tasks": selection_arr
        }

        storeDB(success_dict)


# API

app = FastAPI()
redis_client = Redis(host="127.0.0.1", port=6379)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key="secret",
    cookie_name="cookie22",
    backend_type=BackendType.redis,
    backend_client=redis_client
)

@app.get("/run/{word}")
async def root(request: Request, word):
    if word =="":
        return "请输入目标"
    
    G["api"] = True
    
    # Step 1: 基于目标和提示，分析完成目标的步骤（文本形式）
    if word.startswith("http"):
        res = fewShotGoalByUrl(word)
    else:
        res = zeroShotGoal(word)
    
    request.session.update(G)
    
    return {
        "result": "success",
        "task_text": res,
        }

@app.get("/exp/")
async def exp(request: Request):
    G = request.session
    
    # Step 2: 查询是否有相同的经验可以复用
    search_res = searchExperience("goal: {0}\nos_info: {1}".format(G["final_goal"], G["os_info"]))

    if search_res == False:
        # Step 2.1: 没有相同的经验，开始AI分解新任务
        selection_arr = newTask()

        return {
            "result": "human",
            "selection_arr": selection_arr,
        }

    else:
        # Step 2.2: 有相同的经验，直接执行
        G["finded_experience"] = True
        selection_arr = f.jsonFromFile("library/tasks/" + search_res + ".json")["tasks"]
        print(selection_arr)

    G["selection_arr"] = selection_arr

    request.session.update(G)

    return {
        "result": "success",
        "selection_arr": selection_arr,
    }

@app.get("/get/")
async def get(request: Request):
    return request.session