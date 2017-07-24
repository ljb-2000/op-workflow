#!/bin/sh
base_dir=$(cd $(dirname $0);pwd)
echo sh $0 $*
echo "脚本开始执行"
ret=$(python $base_dir/get_task_data.py $1)
user=$(echo "$ret"|grep -Po '(?<="creator": ")[^"]*')
envs=$(echo "$ret"|grep -Po '(?<="cicd_env": \[)[^\]]*')
echo "task_mark_percent=10"
for env in $(echo $envs|tr -d '",')
do
ssh hz-jenkins-m01 "grep -q ^$user$ /opt/cicd_auth/$env ||echo $user >>/opt/cicd_auth/$env"
done
ssh hz-jenkins-m01 "cd /opt/cicd_auth && git add . && git commit -am \"add $user\" && git push"
echo "task_mark_percent=100"
echo "脚本已执行完成"
