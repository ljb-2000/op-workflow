#coding:utf-8

import re
import sys
import json
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.http import urlquote
from django.db.models import Q
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template.defaulttags import register
from mysite.comm import *
from workflow.models import Task, Task_log, Work_order
from django.conf import settings
from .models import *

reload(sys)
sys.setdefaultencoding('utf-8')


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

def require_role(role_list=[]):
    def _deco(func):
        def __deco(request, *args, **kwargs):
            roles = []
            user = request.user
            roles = [row.name for row in user.role_set.all()]
            if user.is_superuser: roles.append('superuser')
            allow_list = list(set(role_list).intersection(set(roles)))
            if not allow_list:
                return HttpResponse('无权限访问')
            return func(request, *args, **kwargs)
        return __deco
    return _deco

def get_roles_by_username(username):
    user = User.objects.get(username=username)
    roles = [row.name for row in user.role_set.all()]
    if user.is_superuser: roles.append('superuser')
    return roles

def get_role_name():
    roles = Role.objects.all()
    role_dict = {}
    role_dict[0] = "发起人确认"
    for role in roles:
        role_dict[role.id] = role.zh_name
    return role_dict

def health(request):
    response = HttpResponse('ok')
    return response

@login_required
def index(request):
    user = request.user
    username = user.username
    userzhname = user.last_name
    usermail = user.email
    is_superuser = user.is_superuser

    if "modename" in request.session:
        modename = request.session["modename"]
    else:
        #登录默认页为待处理工单
        request.session['modename'] = modename = 'workflow/waiting_task'
    #workflow
    roles = get_roles_by_username(username)
    if 'workflow_admin' in roles: is_workflow_admin = 1
    if 'workflow_supervisor' in roles: is_workflow_supervisor = 1
    if 'superuser' in roles: is_workflow_admin = is_workflow_supervisor = is_ldap_admin = 1
    if 'op' in roles: is_op = 1
    task_num_dict = {}
    task_id_list = [ row.task_id for row in Task_log.objects.filter(username=username).distinct()]
    task_num_dict['done_num'] = Task.objects.filter(id__in=task_id_list).count()
    task_num_dict['waiting_num'] = Task.objects.filter(Q(cur_users__contains=username+';')|Q(cur_user=username)).count()
    task_num_dict['all_num'] = Task.objects.all().count()
    task_num_dict['sent_num'] = Task.objects.filter(creator=username).count()
    task_num_dict['supervisor_num'] = Task.objects.filter(Q(state=2)|Q(state=3)).count()
    return render_to_response('main/index.html',locals())

def login(request):
    user = request.user
    redirect_uri = request.GET.get('next')
    if not redirect_uri: redirect_uri = '/'
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        code = request.POST.get('code')
        user = auth.authenticate(username=username,password=password)
        if user is not None:
            auth.login(request,user)
            return HttpResponseRedirect(redirect_uri)
        else:
            passwd_err = "用户名或密码错误！"
            return render_to_response('main/login.html',locals())
    return render_to_response('main/login.html')

def logout(request):
    user = request.user
    auth.logout(request)
    return HttpResponseRedirect('/login')

@login_required
def updatemain(request):
    treeid = request.session['treeid'] = request.GET.get('treeid',)
    modename = request.session['modename'] = request.GET.get('modename',)
    return HttpResponse('ok')

#role
@login_required
@require_role(role_list=['superuser'])
def add_role(request):
    title = '添加角色'
    users = User.objects.all()
    return render_to_response('main/add_role.html', locals())

@login_required
@require_role(role_list=['superuser'])
def edit_role(request):
    title = '编辑角色'
    id = request.GET.get('id').strip()
    if id:
        users = User.objects.all()
        ret = Role.objects.get(id=int(id))
    else:
        return HttpResponse('参数错误')
    return render_to_response('main/edit_role.html', locals())

@login_required
@require_role(role_list=['superuser'])
def role_list(request):
    title = '系统角色列表'
    key = request.GET.get('key','').strip()
    rets = Role.objects.all()
    if key:
        rets = Role.objects.filter(Q(name__contains=key)|Q(zh_name__contains=key)|Q(desc__contains=key))
    msgnum = rets.count()
    pagenum = settings.PAGE_LIMIT
    return render_to_response('main/role_list.html',locals())

@login_required
@require_role(role_list=['superuser'])
def ajax_role(request):
    user = request.user
    ret = False
    if request.method == 'POST':
        act = request.POST.get('act')
        role_id = request.POST.get('role_id')
        name = request.POST.get('name')
        zh_name = request.POST.get('zh_name')
        desc = request.POST.get('desc')
        users = request.POST.get('users')
        if act == 'add':
            user_list = users.split(',')
            user_obj = User.objects.filter(username__in=user_list)
            ret = Role.objects.create(name=name, zh_name=zh_name, desc=desc, creator=user.username)
            role_obj = Role.objects.get(id=ret.id)
            role_obj.users.add(*user_obj)
            if ret: ret = '添加成功'
        elif act == 'del':
            #workflow中的审批角色不能删除
            if Work_order.objects.filter(Q(flow=role_id)|Q(flow__contains='-%s-' % role_id)|Q(flow__startswith='%s-' % role_id)|Q(flow__endswith='-%s' % role_id)) or Task.objects.filter(Q(flow=role_id)|Q(flow__contains='-%s-' % role_id)|Q(flow__startswith='%s-' % role_id)|Q(flow__endswith='-%s' % role_id)):
                ret = '该角色在workflow中已使用，不能删除'
            else:
                ret = Role.objects.filter(id=role_id).delete()
                if ret: ret = '删除成功'
        elif act == 'edit':
            user_list = users.split(',')
            user_obj = User.objects.filter(username__in=user_list)
            ret = Role.objects.filter(id=role_id).update(name=name, zh_name=zh_name, desc=desc)
            role_obj = Role.objects.get(id=role_id)
            role_obj.users = user_obj
            role_obj.save()
            if ret: ret = '修改成功'
        else:
            ret = '参数错误'
    return HttpResponse(ret)

@login_required
def get_role_users(request):
    users = []
    role_name = request.GET.get('role_name').strip()
    try:
        role = Role.objects.get(name=role_name)
    except:
        return HttpResponse('角色名不存在')
    users = role.users.all()
    users = [row.username for row in users]
    return HttpResponse(json.dumps(users))

@login_required
def get_user_roles(request):
    user = request.user
    roles = [row.name for row in user.role_set.all()]
    if user.is_superuser: roles.append('superuser')
    return HttpResponse(json.dumps(roles))
