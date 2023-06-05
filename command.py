import app.main
import sys

if len(sys.argv) == 1:
    print("请输入Github项目地址 或 搭建环境的目标")
    exit()

input_str = sys.argv[1]

app.main.run(input_str)