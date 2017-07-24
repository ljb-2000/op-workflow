#coding:utf-8

import time
import os
import json
import re
import requests
from celery import task,platforms
from django.contrib.auth.models import User
from django.conf import settings
from main.models import *
from mysite.comm import *
from .models import *

platforms.C_FORCE_ROOT = True

@task()
def exec_task(task_id):
    ret = Task.objects.get(id=task_id)
    title = ret.title
    state = ret.state
    work_order_id = ret.work_order_id
    work_order_name = Work_order.objects.get(id=work_order_id).name
    creator = ret.creator
    user_info = User.objects.get(username=creator)
    script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
    log_file = '%s/logs/workflow/%d.log' % (settings.BASE_DIR, task_id)
    cmd = 'sh %s/%s.sh %s &>%s' % (script_dir, work_order_name, task_id, log_file)
    ret, err = local_cmd(cmd)
    tolist = [user_info.email]
    subject = '<%s>工单进度通知' % title
    content = '<br>您好！<br>%s 工单任务已处理，等待您确认，<a href="%s/workflow/edit_task?id=%d&state=%d" target="_blank">点击此处查看处理</a>，谢谢！' % (title, settings.SYS_API, task_id, state)
    print send_html_mail(tolist, subject, content)
    return task_id




