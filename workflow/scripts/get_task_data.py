#coding=utf-8

import sys
import os
import json
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.core.management import execute_from_command_line
from workflow.models import *

task_id = sys.argv[1]
ret = Task.objects.get(id=task_id)
datas = {}
datas['creator'] = ret.creator
datas['data'] = json.loads(ret.data)

print json.dumps(datas)
