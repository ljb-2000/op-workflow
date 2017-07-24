#!/bin/sh
base_dir=$(cd $(dirname $0);pwd)
echo sh $0 $*
echo "脚本开始执行"
ret=$(python $base_dir/get_task_data.py $1)
user=$(echo "$ret"|grep -Po '(?<="creator": ")[^"]*')
echo "task_mark_percent=10"
echo "申请人是$user"
echo "task_mark_percent=100"
echo "脚本已执行完成"
