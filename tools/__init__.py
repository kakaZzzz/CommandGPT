from langchain.utilities import PythonREPL, BashProcess
from .shell import Shell

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
        }
    
    def run(self, tool, command):
        return self.cache[tool]["func"](command)

    def inline_text(self, tools):
        text = f"你只能使用以下{len(tools)}个工具来完成任务:\n"
        index = 1
        for tool in tools:
            text += f"{index}. {tool}. Description: {self.cache[tool]['description']}\n"
            index = index + 1
        print(text)
        return text

# Tools().inline_text(["shell", "python_repl"])