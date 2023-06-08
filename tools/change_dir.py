from subprocess import PIPE,Popen
import app.functions as f
import os

class ChangeDir():
    def __init__(self):
        pass

    def run(self, command):
        print(command)
        try:
            os.chdir(command.split(" ")[1])
            f.yellowPrint("[info]当前目录是: ", os.getcwd())
            return True
        except Exception as e:
            f.redPrint("[error]切换目录失败: ", e)
            return False