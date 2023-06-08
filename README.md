# CommandGPT

### 配置openai api key

```
cp .env_example .env
vi .env
```

填写你自己的api key

```
OPENAI_API_KEY = ""
```

### 安装依赖库

```
pip install -r requirements.txt
```

### 使用

```
python command.py 帮我用pip安装pillow库
```

or

```
python command.py https://github.com/reworkd/AgentGPT
```
