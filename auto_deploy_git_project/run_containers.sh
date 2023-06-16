#!/bin/bash

# 参数:
# $1 - AGILE_RELEASE_VERSION

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <AGILE_RELEASE_VERSION>"
  exit 1
fi

AGILE_RELEASE_VERSION="$1"
IMAGE_NAME="auto-deploy-git:v1.0"
SCRIPT="deploy_git_repo"
COMMAND_FILE="command_file"
COMMAND_COUNT=`wc -l $COMMAND_FILE | awk -F ' ' '{print $1}'`
DEPLOYDIR="/home/work/workspace/auto_git"

# Define the maximum number of concurrent executions
max_concurrent=5
# Define the timeout
timeout_seconds=$((30*60))

execute_docker_task() {
  index=$1

  # 获取命令
  line=`sed -n ${index}p $COMMAND_FILE`

  # 获取repo full_name
  FULL_NAME=`sed -n ${index}p $COMMAND_FILE | awk -F ' ' '{print $1}' | sed 's/\//_/'`

  # 容器命名
  # TODO:同一个任务目前只能运行1个容器，无法执行多次，需考虑
  CONTAINER_NAME="$FULL_NAME-$AGILE_RELEASE_VERSION"
  echo "Container $CONTAINER_NAME started and command executed."

  # 创建并启动容器
  docker run -id -v $DEPLOYDIR/vector_store_db:/home/vector_store_db -v $DEPLOYDIR/repo_data:/home/repo_data -v $DEPLOYDIR/log:/home/log --name $CONTAINER_NAME $IMAGE_NAME

  # 将文件复制到容器内
  docker cp $SCRIPT $CONTAINER_NAME:/home/

  # 在容器内执行命令
  timeout $timeout_seconds docker exec -i $CONTAINER_NAME /bin/bash -c "cd /home/$SCRIPT && python main.py $line>/home/log/$FULL_NAME.log 2>&1"

  # 删除容器
  docker rm -f $CONTAINER_NAME
  echo "Container $CONTAINER_NAME stopped."
}

i=0
while [ $i -le $COMMAND_COUNT ]
do
  echo "exec $i/$COMMAND_COUNT command in container"
  let i=i+1
  while [ $(jobs -r | wc -l) -ge $max_concurrent ]; do
    sleep 1
  done

  execute_docker_task $i &
done

# TODO：未来修改执行任务，执行前临时先手动清理一下log，长远需要考虑一下解决方案，防止日志留存的影响
# 备份日志
cd $DEPLOYDIR/log
mkdir $AGILE_RELEASE_VERSION
cp *.log $AGILE_RELEASE_VERSION

