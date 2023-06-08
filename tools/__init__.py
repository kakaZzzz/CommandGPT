from langchain.utilities import PythonREPL, BashProcess
from .shell import Shell
from .change_dir import ChangeDir
import app.functions as f

class Tools:
    def __init__(self):

        self.cache = {

            "shell": {
                "description": "Executes commands in a terminal. Input should be valid commands, and the output will be any output from running that command.",
                "func": Shell().run
            },

            "python_repl": {
                "description": "A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
                "func": PythonREPL().run
            },

            "change_dir": {
                "description": "Changes the current directory. Input should be a valid directory path.",
                "func": ChangeDir().run
            },
        }
    
    def run(self, tool, command):
        return self.cache[tool]["func"](command)

    def count(self):
        return len(self.cache)

    def inline_text(self, tools):
        text = f"你只能使用以下{len(tools)}个工具来完成任务:\n"
        index = 1
        for tool in tools:
            text += f"{index}. Tool name:{tool}. Description: {self.cache[tool]['description']}\n"
            index = index + 1
        print(text)
        return text
    
    def decompose(self, item):
        if item["tool"] == "shell":
            res = self.run("shell", item["command"])
            print(res)
        elif item["tool"] == "human":
            f.yellowPrint("reasoning: ", item["reasoning"])
            f.yellowPrint("command: ", item["command"])
            f.bluePrint(">>> 请按照提示进行人工操作，执行完毕后按回车键继续")
            return "continue"
        elif item["tool"] == "python_repl":
            res = self.run("python_repl", item["command"])
        elif item["tool"] == "change_dir":
            res = self.run("change_dir", item["command"])

        return res

# Tools().inline_text(["shell", "python_repl"])