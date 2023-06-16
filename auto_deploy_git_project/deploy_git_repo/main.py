import datetime
import random
import os
import re
import shutil
import sys
from typing import Any, Dict, List, Union

# Langchain imports
from langchain import LLMChain, OpenAI, SerpAPIWrapper
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.tools import ShellTool
from langchain.prompts import BaseChatPromptTemplate
from langchain.schema import AgentAction, AgentFinish, HumanMessage, BaseMessage
from langchain.text_splitter import MarkdownTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import GitLoader, UnstructuredMarkdownLoader
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult
from langchain.callbacks.base import AsyncCallbackHandler

# 关闭TOKENIZERS_PARALLELISM
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 翻墙代理
os.environ['https_proxy'] = 'http://10.8.5.5:3128'
# os.environ['HTTPS_PROXY'] = 'http://10.8.5.5:3128'

# openai 相关key&代理配置
# weiwei key
# OPENAI_API_KEY='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'
# guozhen key
# OPENAI_API_KEY='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'
# ximing key
# OPENAI_API_KEY='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'
# xiyang key
OPENAI_API_KEY = 'sk-ZZ72KHNYXBMMnSwtqN5cT4M5ehcJFfVK1ChHmT9q1R94p1RM'
OPENAI_API_BASE = 'https://api.chatanywhere.cn/v1'
os.environ['OPENAI_API_BASE'] = OPENAI_API_BASE
os.environ['SERPAPI_API_KEY'] = 'e37ef0fbc8ce5e5f0e375a7fa11382afa677b86ffdd38a7208cc2dade6a31f7f'

# 解析命令行参数
if len(sys.argv) != 4:
    print("should give fullname, branch, query")
    sys.exit(1)
[_, fullname, branch, query] = sys.argv


# 初始化llm, 大的 temperature 会让输出有更多的随机性
llm_gpt3 = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
llm_gpt4 = ChatOpenAI(temperature=0, model_name="gpt-4", openai_api_key=OPENAI_API_KEY)
llm = llm_gpt4

# 初始化vector store
# vector_store_name = "LLM_LANGCHAIN"
# vector_store_db = Chroma(collection_name=vector_store_name, persist_directory="./vector_store_db/LLM_LANGCHAIN")
vector_store_name = "langchain_" + fullname.replace("/", "_")
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vector_store_db = Chroma(collection_name=vector_store_name,
                         persist_directory="./vector_store_db/langchain_store",
                         embedding_function=embeddings)

# Set up the prompt with input variables for tools, user input and a scratchpad for the model to record its workings
template = """I want you to act as an operation expert for installing components.
Try to find the installation method of the component and execute the installation using shell.
Determine whether yes is required during installation, and add the yes parameter if necessary.

Your machine environment in the Docker container is as follows:
Operating System: Debian GNU/Linux 11
Python Version: Python 3.10
Go Version: go1.20
Conda Version: conda 23.5.0

You have access to the following tools:

{tools}

You should respond only in the format as described below
Response Format:

Question: the input component you must install
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat n times)
Thought: I now know the result
Final Result: You must output the final result to the original input

Begin! Remember to give detailed, informative answers

New question: install {input}
{agent_scratchpad}"""


# Set up a prompt template
class CustomPromptTemplate(BaseChatPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]

    def format_messages(self, **kwargs) -> List[BaseMessage]:
        # Get the intermediate steps (AgentAction, Observation tuples)

        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            observation_tail = observation[-1000:]
            thoughts += f"\nObservation: {observation_tail}\nThought: "

        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts

        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])

        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]


class CustomOutputParser(AgentOutputParser):
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:

        # Check if agent should finish
        if "Final Result:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Result:")[-1].strip()},
                log=llm_output,
            )

        # Parse out the action and action input
        regex = r"Action: (.*?)[\n]*Action Input:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)

        # If it can't parse the output it raises an error
        # You can add your own logic here to handle errors in a different way i.e. pass to a human, give a canned response
        if not match:
            # raise ValueError(f"Could not parse LLM output: `{llm_output}`")
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": 'Final: ' + llm_output},
                log=llm_output,
            )
        action = match.group(1).strip()
        action_input = match.group(2)

        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)


class MyCustomSyncHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs):
        print(f"Sync Executor token: {token}")
        
    def on_text(self, text: str, **kwargs):
        print(f"\nSync Executor text: {text}")
    
    def on_tool_end(self, output: str, **kwargs) -> Any:
        print(f"\nAction End Output: {output}")
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> Any:
        print(f"\nAction Start Input:: {input_str}")


def test_llm():
    text = "what is the results of 5+6?"
    # 返回 11
    print(llm(text))


def record_git_readme_document(fullname, branch="master", use_cache=True):
    git_url = f"https://github.com/{fullname}"
    if use_cache:
        repo_path = f"./repo_data/{fullname}/cache/"
    else:
        cur_time = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        random_num = random.randint(0, 100)
        repo_path = f"./repo_data/{fullname}/{cur_time}_{random_num}"

    # 数据下载
    readme_file = f"{repo_path}/README.md"
    readme_file_rst = f"{repo_path}/README.rst"
    if use_cache and (os.path.exists(readme_file) or os.path.exists(readme_file_rst)):
        print(f"repo_path[{readme_file}] already exist, use cache")
    else:
        # 清空目录
        # if os.path.exists(repo_path):
        #     print(f"repo_path[{repo_path}] already exist, rm it")
        #     shutil.rmtree(repo_path)
        
        # 初始化loader
        git_loader = GitLoader(
            clone_url=git_url,
            repo_path=repo_path,
            branch=branch,
            file_filter=lambda file_path: file_path.endswith(".md")
        )
        git_loader.load()
    
    if not os.path.exists(readme_file):
        readme_file = readme_file_rst
    # readme解析
    data_loader = UnstructuredMarkdownLoader(readme_file)
    documents = data_loader.load()

    # readme内容分割
    markdown_splitter = MarkdownTextSplitter(chunk_size=2000, chunk_overlap=0)
    docs = markdown_splitter.split_documents(documents)
    vector_store_db.add_documents(docs)


def expand_tools():
    # chain_type = "stuff"
    chain_type = "refine"
    podcast_retriever = RetrievalQA.from_chain_type(llm=llm_gpt3, chain_type=chain_type,
                                                    retriever=vector_store_db.as_retriever())
    shell_tool = ShellTool()
    search = SerpAPIWrapper()
    expanded_tools = [
        Tool(
            name='Knowledge Base',
            func=podcast_retriever.run,
            description="Useful for general questions about how to do things and for details on interesting topics. Input should be a fully formed question."
        ),
        Tool(
            name='shell',
            func=shell_tool.run,
            description="useful for when you need to exec command."
        ),
        Tool(
            name = 'Shell',
            func=shell_tool.run,
            description="useful for when you need to exec command.",
        ),
        Tool(
            name = "Search",
            func=search.run,
            description="useful for when you need to answer questions about current events"
        )
    ]
    return expanded_tools


def test_db():
    query = "安装 langchain"
    docs = vector_store_db.similarity_search(query)
    print(docs)


record_git_readme_document(fullname, branch=branch)
expanded_tools = expand_tools()
prompt = CustomPromptTemplate(
    template=template,
    tools=expanded_tools,
    # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
    # This includes the `intermediate_steps` variable because that is needed
    # TODO: https://www.rstk.cn/news/70865.html?action=onClick
    input_variables=["input", "intermediate_steps"]
)
output_parser = CustomOutputParser()
# LLM chain consisting of the LLM and a prompt
llm_chain = LLMChain(llm=llm, prompt=prompt, callbacks=[MyCustomSyncHandler()])

# Using tools, the LLM chain and output_parser to make an agent
tool_names = [tool.name for tool in expanded_tools]

agent = LLMSingleActionAgent(
    llm_chain=llm_chain,
    output_parser=output_parser,
    # We use "Observation" as our stop sequence so it will stop when it receives Tool output
    # If you change your prompt template you'll need to adjust this as well
    stop=["\nObservation:"],
    allowed_tools=tool_names
)
agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=expanded_tools, verbose=True, max_execution_time=None)
agent_executor.run(query)

