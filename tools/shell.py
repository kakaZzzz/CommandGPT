from subprocess import PIPE,Popen
import app.functions as f

class Shell():
    def __init__(self):
        pass

    def run(self, command):
        print("执行命令：", command)
        p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

        while p.poll() is None:
            line = p.stdout.readline().decode('utf-8')
            print( line )

        stdout, stderr = p.communicate()
        print("输出信息：", stdout.decode("utf-8"))
        f.redPrint("错误信息：", stderr.decode("utf-8"))
        print("返回码：", p.returncode)
        return """
returncode是：
{0}

输出信息是：
{1}

错误信息是：
{2}
""".format(p.returncode, stdout.decode("utf-8"), stderr.decode("utf-8"))