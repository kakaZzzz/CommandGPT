import sys
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain

from langchain.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

import os
import re
from subprocess import PIPE,Popen
import requests

def getGithubRepo(url):
    matchObj = re.search( r'com/(.*)$', url, re.M|re.I)
    if matchObj:
        return "https://raw.githubusercontent.com/"+matchObj[1]+"/main/README.md"


# 命令行参数
if len(sys.argv) == 1:
    print("请输入Github项目地址")
    exit()

url = sys.argv[1]

readme = getGithubRepo(url)
print( "readme地址:", readme )

print( "抓取readme..." )
readme = requests.get(readme)
# print("HTML:\n", readme.text)

# exit(0)

# api keys

os.environ["OPENAI_API_KEY"] = "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"

llm = ChatOpenAI(temperature=0.9, streaming=True)

# prompt templates
system_message_prompt = SystemMessagePromptTemplate.from_template("你是一个专业的程序员，能帮助完成编程相关的事情")

chinese_autogpt_prompt = HumanMessagePromptTemplate.from_template("""
{readme}

目标:

分析以上的文本，我使用mac电脑，告诉我如何通过命令行安装该项目

Human: 一步一步完成目标:
""")
                                                                  
                                                                  
debugger_prompt = HumanMessagePromptTemplate.from_template("""
执行的命令是：
{command}

运行后错误信息是：
{error_message}

目标:

分析以上的错误信息，我使用mac电脑，告诉我如何通过命令行解决该错误

Human: 一步一步完成目标，代码用markdown语法展示:
""")

# chain
chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, chinese_autogpt_prompt])
chain = LLMChain(llm=llm, prompt=chat_prompt)

debugger_chain = LLMChain(llm=llm, prompt=ChatPromptTemplate.from_messages([system_message_prompt, debugger_prompt]))

#run

print( "GPT分析安装步骤..." )
s = chain.run({
        'readme': readme.text
    })

print( s)

# s="""

# 2. 添加 k8sgpt 的 tap：

# $$ brew tap k8sgpt-ai/k8sgpt

# 3. 安装 k8sgpt：

# $$ brew install k8sgpt
# """

# matchObj = re.findall( r'\$\$(.*)$', s, re.M|re.I)
matchObj = re.findall( r'```([^`]*)```', s, re.M|re.I|re.S)
if matchObj:
   for match in matchObj:
        # print(match)
        print("执行: "+match)
        print("###")
        proc = Popen(
            match,  # cmd特定的查询空间的命令
            stdin=None,  # 标准输入 键盘
            stdout=PIPE,  # -1 标准输出（演示器、终端) 保存到管道中以便进行操作
            stderr=PIPE,  # 标准错误，保存到管道
            shell=True)
        # print(proc.communicate()) # 标准输出的字符串+标准错误的字符串
        outinfo, errinfo = proc.communicate()
        print("Info:")
        print("\033[93m"+outinfo.decode('utf-8')+"\033[0m")
        print("Error:")
        print("\033[91m"+errinfo.decode('utf-8')+"\033[0m")

        proc.wait()
        if  proc.returncode == 1:
            print("执行失败，调用GPT尝试解决错误问题")
            print("###")
            s = debugger_chain.run({
                'error_message': outinfo.decode('utf-8'),
                'command': match
                })
            print("解决方法:")
            print("###")
            print("\033[93m"+s+"\033[0m")
            print("###")
            print("任务退出，请先解决卡点问题")
            break
        else:
            print(proc.returncode)
else:
   print("No match!!")
