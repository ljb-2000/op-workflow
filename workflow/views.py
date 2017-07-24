#coding:utf-8
import os
import re
import json
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.template.defaulttags import register
from django.contrib.auth.decorators import login_required
from django.conf import settings
from main.models import *
from mysite.comm import *
from main.views import *
from .tasks import exec_task
from .models import *

logger = logging.getLogger(__name__)

@register.filter
def get_flow_names(flow):
    flow_names = '免审批'
    flow_id_list = flow.split('-')
    if flow_id_list[0]:
        flow_name_list = [Role.objects.get(id=role_id).zh_name for role_id in flow_id_list]
        flow_names = '->'.join(flow_name_list)
    return flow_names

@login_required
@require_role(role_list=['workflow_admin'])
def order_list(request):
    title = '工作流列表'
    username = request.user.username
    key = request.GET.get('key','').strip()
    if key:
        rets = Work_order.objects.filter(Q(name__contains=key)|Q(title__contains=key)|Q(desc__contains=key)|Q(creator__contains=key))
    else:
        rets = Work_order.objects.order_by('-id')
    msgnum = rets.count()
    pagenum = settings.PAGE_LIMIT
    return render_to_response('workflow/order_list.html',locals())


@login_required
@require_role(role_list=['workflow_admin'])
def add_order(request):
    title = '添加工作流'
    username = request.user.username
    roles = Role.objects.all()
    return render_to_response('workflow/add_order.html',locals())

@login_required
@require_role(role_list=['workflow_admin'])
def edit_order(request):
    title = '编辑工作流'
    username = request.user.username
    roles = Role.objects.all()
    id = request.GET.get('id','').strip()
    if not id: return HttpResponse('参数错误')
    try:
        ret = Work_order.objects.get(id=int(id))
    except:
        return HttpResponse('id不存在')
    if ret.flow:
        role_ids = [int(row) for row in ret.flow.split('-')]
    else:
        role_ids = []
    return render_to_response('workflow/edit_order.html',locals())

@login_required
@require_role(role_list=['workflow_admin'])
def ajax_order(request):
    username = request.user.username
    if request.method == 'POST':
        result = False
        act = request.POST.get('act','').strip()
        if act == 'add':
            name = request.POST.get('name','').strip()
            if Work_order.objects.filter(name=name): return HttpResponse('工单名已存在')
            title = request.POST.get('title','').strip()
            desc = request.POST.get('desc','')
            is_active = int(request.POST.get('is_active',''))
            flow = request.POST.get('flow','')
            ret = Work_order.objects.create(name=name, title=title, desc=desc, flow=flow, creator=username, is_active=is_active)
            if ret:
                result = '添加成功'
                templates_dir = "%s/mysite/templates/workflow" % settings.BASE_DIR
                scripts_dir = "%s/workflow/scripts" % settings.BASE_DIR
                os.system("cd %s;test -f %s_form.html || \cp demo_form.html %s_form.html" % (templates_dir, name, name))
                os.system("cd %s;test -f %s.sh || \cp demo.sh %s.sh" % (scripts_dir, name, name))
        elif act == 'edit':
            name = request.POST.get('name','').strip()
            title = request.POST.get('title','').strip()
            desc = request.POST.get('desc','')
            is_active = int(request.POST.get('is_active',''))
            flow = request.POST.get('flow','')
            ret = Work_order.objects.filter(name=name).update(title=title, desc=desc, flow=flow, creator=username, is_active=is_active)
            if ret: result = '修改成功'
        elif act == 'del':
            id = request.POST.get('id','').strip()
            order_obj = Work_order.objects.filter(id=id)
            ret = order_obj.delete()
            if ret: result = '删除成功'
    return HttpResponse(result)    

@login_required
def link_task(request):
    title = '事项列表'
    username = request.user.username
    rets = Work_order.objects.filter(is_active=1)
    return render_to_response('workflow/link_task.html',locals())

@login_required
@require_role(role_list=['workflow_supervisor'])
def supervisor_task(request):
    title = '督办事项'
    username = request.user.username
    orders = Work_order.objects.all()
    key = request.GET.get('key','').strip()
    if key:
        rets = Task.objects.filter(Q(state=2)|Q(state=3),Q(title__contains=key)|Q(creator__contains=key)|Q(data__contains=key)).order_by('-id')
    else:
        rets = Task.objects.filter(Q(state=2)|Q(state=3)).order_by('-id')
    msgnum = rets.count()
    pagenum = settings.PAGE_LIMIT
    role_dict = get_role_name()
    state_dict = settings.TASK_STATE_DICT
    return render_to_response('workflow/supervisor_task.html',locals())

@login_required
def waiting_task(request):
    title = '待办事项'
    username = request.user.username
    orders = Work_order.objects.all()
    key = request.GET.get('key','').strip()
    if key:
        rets = Task.objects.filter((Q(cur_users__contains=username+';')|Q(cur_user=username)),Q(title__contains=key)|Q(creator__contains=key)|Q(data__contains=key)).order_by('-id')
    else:
        rets = Task.objects.filter(Q(cur_users__contains=username+';')|Q(cur_user=username)).order_by('-id')
    msgnum = rets.count()
    pagenum = settings.PAGE_LIMIT
    role_dict = get_role_name()
    state_dict = settings.TASK_STATE_DICT
    return render_to_response('workflow/waiting_task.html',locals())

@login_required
def sent_task(request):
    title = '已发事项'
    username = request.user.username
    orders = Work_order.objects.all()
    key = request.GET.get('key','').strip()
    if key:
        rets = Task.objects.filter(Q(creator=username),Q(title__contains=key)|Q(creator__contains=key)|Q(data__contains=key)).order_by('-id')
    else:
        rets = Task.objects.filter(creator=username).order_by('-id')
    msgnum = rets.count()
    pagenum = settings.PAGE_LIMIT
    role_dict = get_role_name()
    state_dict = settings.TASK_STATE_DICT
    return render_to_response('workflow/sent_task.html',locals())

@login_required
@require_role(role_list=['workflow_supervisor'])
def all_task(request):
    title = '所有事项'
    username = request.user.username
    orders = Work_order.objects.all()
    key = request.GET.get('key','').strip()
    if key:
        rets = Task.objects.filter(Q(title__contains=key)|Q(creator__contains=key)|Q(data__contains=key)).order_by('-id')
    else:
        rets = Task.objects.order_by('-id')
    msgnum = rets.count()
    pagenum = settings.PAGE_LIMIT
    role_dict = get_role_name()
    state_dict = settings.TASK_STATE_DICT
    return render_to_response('workflow/all_task.html',locals())

@login_required
def done_task(request):
    title = '已办事项'
    username = request.user.username
    orders = Work_order.objects.all()
    rets = Task_log.objects.filter(username=username)
    task_id_list = [ row.task_id for row in rets]
    task_id_list = list(set(task_id_list))
    key = request.GET.get('key','').strip()
    if key:
        rets = Task.objects.filter(~Q(creator=username),Q(id__in=task_id_list),Q(title__contains=key)|Q(creator__contains=key)|Q(data__contains=key)).order_by('-id')
    else:
        rets = Task.objects.filter(~Q(creator=username),Q(id__in=task_id_list)).order_by('-id')
    msgnum = rets.count()
    pagenum = settings.PAGE_LIMIT
    role_dict = get_role_name()
    state_dict = settings.TASK_STATE_DICT
    return render_to_response('workflow/done_task.html',locals())

def get_task_info(request):
    """获取任务信息"""
    id = request.GET.get('id','').strip()
    datas = {}
    if id:
        try:
            ret = Task.objects.get(id=int(id))
            datas['creator'] = ret.creator
            datas['data'] = json.loads(ret.data)
        except:
            pass
    return HttpResponse(json.dumps(datas))

@login_required
def del_task(request):
    """申请人在已发事项列表中撤销工单 申请人在待办事项列表中回退修改的工单可撤销工单"""
    id = request.GET.get('id','').strip()
    if not id: return HttpResponse('参数错误')
    username = request.user.username
    id = int(id)
    ret = Task.objects.get(id=id)
    creator = ret.creator
    cur_user = ret.cur_user
    cur_state = ret.state
    #申请人提交后未被第一个审批角色处理之前还能撤销
    if creator == username and cur_state <= 2:
        cur_role_id = -1
        cur_users = cur_user = act_opinion = ''
        state = role_id = act_type = 0 
        Task.objects.filter(id=id).update(state=state, cur_role_id=cur_role_id, cur_users=cur_users, cur_user=cur_user)
        Task_log.objects.create(task_id=id,username=username,role_id=role_id,act_type=act_type,act_opinion=act_opinion)
        result = '已撤销'
    #审批人已经审批后申请人不能主动撤销，只能由审批人撤销
    elif creator == username and cur_state > 2:
        result = '已进入处理流程，不能撤销，请联系当前处理人进行撤销'
    else:
        result = '您无权撤销'
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
@require_role(role_list=['workflow_supervisor'])
def unlock_task(request):
    """督办人解除锁定审批人"""
    username = request.user.username
    id = request.GET.get('id','').strip()
    if id:
        id = int(id)
        try:
            ret = Task.objects.get(id=id)
            cur_user = ret.cur_user
            Task.objects.filter(id=id).update(cur_user='')
        except:
            return HttpResponse('id不存在')
    else:
        return HttpResponse('数错误')
    return HttpResponseRedirect('/workflow/supervisor_task/')

@login_required
def ajax_task(request):
    user = request.user
    username = user.username
    is_supervisor = 0
    #判断是否有督办权限
    roles = [row.name for row in user.role_set.all()]
    if 'workflow_supervisor' in roles: 
        is_supervisor = 1
        admin_role_id = Role.objects.get(name='workflow_supervisor').id
    if request.method == 'POST':
        act = request.POST.get('act','').strip()
        #提交工单
        if act == 'add':
            task_id = request.POST.get('task_id','').strip()
            creator = request.POST.get('creator','').strip()
            creator_name = user.last_name
            creator_mail = user.email
            next_role_id = int(request.POST.get('next_role_id').strip())
            next_user = request.POST.get('next_user','').strip()
            work_order_id = int(request.POST.get('work_order_id').strip())
            #从POST数据中提取form表单中数据
            data = request.POST.lists()
            data = dict(data)
            #删除垃圾数据，保留重要表单中有用的数据
            data.pop('act')
            data.pop('task_id')
            data.pop('creator')
            data.pop('next_role_id')
            if data.has_key('next_user'): 
                data.pop('next_user')
                next_user, next_user_mail = next_user.split('_')
            data.pop('work_order_id')
            work_order_obj = Work_order.objects.get(id=work_order_id)
            work_order_title = work_order_obj.title
            work_order_name = work_order_obj.name
            flow = work_order_obj.flow
            title = creator_name + work_order_title
            #免审批流程
            if next_role_id == 0:
                next_state = 4
                next_users = creator + ';'
                data = json.dumps(data)
                ret = Task.objects.create(title=title, creator=creator, work_order_id=work_order_id, flow=flow,
                    data=data, state=next_state, cur_role_id=next_role_id, cur_users=next_users, cur_user='')
                task_id = ret.id
                exec_task.delay(task_id)
                result = '免审批工单已提交'
            #审批流程
            else:    
                next_state = 2
                next_users = Role.objects.get(id=next_role_id).users.all()
                next_users = [row.username for row in next_users]
                next_users = ';'.join(next_users) + ';'
                #业务树权限管理有独立的角色管理，忽略工作流中的角色
                if work_order_name == 'mtree_role': next_users = data.pop('users')[0]
                data = json.dumps(data)
                #工单被驳回修改后提交有task_id参数
                if task_id:
                    task_id = int(task_id)
                    Task.objects.filter(id=task_id,state__lte=2).update(title=title, creator=creator, work_order_id=work_order_id, flow=flow,
                        data=data, state=next_state, cur_role_id=next_role_id, cur_users=next_users, cur_user='')
                #全新创建提交工单
                else:
                    ret = Task.objects.create(title=title, creator=creator, work_order_id=work_order_id, flow=flow, 
                        data=data, state=next_state, cur_role_id=next_role_id, cur_users=next_users, cur_user='')
                    task_id = ret.id 
                #给审批人发送工单处理通知
                tolist = [next_user_mail]
                subject = '<%s>工单处理通知' % title
                content = '<br>您好！<br>%s 工单任务已发起，等待您处理，<a href="%s/workflow/edit_task?id=%d" target="_blank">点击此处查看处理</a>，谢谢！' % (title, settings.SYS_API, task_id)
                send_html_mail(tolist, subject, content)
                result = settings.TASK_STATE_DICT[next_state]
        #审批工单
        elif act == 'audit':
            #task_id、act_type和act_opinion是必须参数，act_opinion参数内容可以为空，next_user为可选参数，是当前审批人指定下一位审批人
            task_id  = request.POST.get('task_id','').strip()
            act_type  = request.POST.get('act_type','').strip()
            act_opinion  = request.POST.get('act_opinion','').strip()
            next_user  = request.POST.get('next_user','').strip()
            if not task_id and not act_type: return HttpResponse('参数错误')
            task_id = int(task_id)
            act_type = int(act_type)
            ret = Task.objects.get(id=task_id)
            work_order_id = ret.work_order_id
            title = ret.title
            cur_state = ret.state
            creator = ret.creator
            cur_role_id = ret.cur_role_id
            cur_users = ret.cur_users
            cur_user = ret.cur_user
            user_info = User.objects.get(username=creator)
            creator_name = user_info.last_name
            creator_mail = user_info.email
            flow = ret.flow
            flow_list = flow.split('-')
            #当前审批人是工单申请人时
            if cur_user == creator and cur_state == 4:
                next_role_id = -1
                next_users = next_user = ''
                #撤销
                if act_type == 0: next_state = 0
                #确认
                if act_type == 1: next_state = 5
            #当前审批角色是流程最后一个审批角色时
            elif flow_list.index(str(cur_role_id)) + 1 == len(flow_list):
                #下一个审批角色为申请人
                next_role_id = 0
                #撤销
                if act_type == 0: 
                    next_state = 0
                    next_users = next_user = ''
                #同意
                if act_type == 1: 
                    try:
                        exec_task.delay(task_id)
                    except Exception as e:
                        logger.error("rabbitmq error:" + e)
                        return HttpResponse('添加任务报错了')
                    next_state = 4
                    next_user = creator
                    next_users = creator + ';'
                #驳回,申请人重新修改
                if act_type == 2: 
                    next_state = 1
                    next_user = creator
                    next_users = creator + ';'
            #当前审批角色非最后一个审批角色时
            else:
                #撤销
                if act_type == 0:
                    next_role_id = -1
                    next_state = 0
                    next_users = next_user = ''
                #同意
                elif act_type == 1:
                    next_role_id = flow_list[flow_list.index(str(cur_role_id))+1]
                    next_users = Role.objects.get(id=next_role_id).users.all()
                    tolist = [row.email for row in next_users]
                    next_users = [row.username for row in next_users]
                    next_users = ';'.join(next_users) + ';'
                    #只邮件提醒指定的审批人
                    next_user  = request.POST.get('next_user','').strip()
                    if next_user:
                        next_user, next_user_mail = next_user.split('_')
                        tolist = [next_user_mail]
                    #当前审批人为空则未锁定，同一角色成员都能审批
                    next_state = 3
                #驳回
                elif act_type == 2:
                    next_role_id = 0
                    next_state = 1
                    next_user = creator
                    next_users = creator + ';'
            #督办人员
            if username not in cur_users.split(';') and admin_role_id: cur_role_id = admin_role_id
            Task.objects.filter(id=task_id).update(state=next_state, cur_role_id=next_role_id, cur_users=next_users, cur_user='')
            Task_log.objects.create(task_id=task_id,username=username,role_id=cur_role_id,act_type=act_type,act_opinion=act_opinion)
            #邮件通知
            subject = '<%s>工单处理通知' % title
            to_creator_subject = '<%s>工单进度通知' % title
            result = settings.TASK_STATE_DICT[next_state]
            if next_state == 3: 
                content = '<br>您好！<br>%s 工单任务已审批，等待您审批，<a href="%s/workflow/edit_task?id=%d" target="_blank">点击此处查看处理</a>，谢谢！' % (title, settings.SYS_API, task_id)
                #邮件通知下一位审批人处理
                send_html_mail(tolist, subject, content)
                to_creator_content = '<br>您好！<br>%s 工单任务已由%s审批，等待%s审批，<a href="%s/workflow/show_task?id=%d" target="_blank">点击此处查看进度</a>，谢谢！' % (title, cur_user, next_user, settings.SYS_API, task_id)
                #邮件通知申请人进度
                send_html_mail([creator_mail], to_creator_subject, to_creator_content)
            if next_state == 1: 
                result = '已回退'
                to_creator_content = '<br>您好！<br>%s 工单任务已回退，请修改提交，<a href="%s/workflow/add_task?id=%d" target="_blank">点击此处查看处理</a>，谢谢！' % (title, settings.SYS_API, task_id)
                send_html_mail([creator_mail], to_creator_subject, to_creator_content)
            if next_state == 0: 
                to_creator_content = '<br>您好！<br>%s 工单任务已撤销，<a href="%s/workflow/show_task?id=%d" target="_blank">点击此处查看</a>，谢谢！' % (title, settings.SYS_API, task_id)
                send_html_mail([creator_mail], to_creator_subject, to_creator_content)
        else:
            result = '参数错误'
        return HttpResponse(result)

@login_required
def add_task(request):
    title = '新建事项'
    #查看工单必须包含id参数
    work_order_id = request.GET.get('order_id','').strip()
    task_id = request.GET.get('id','').strip()
    #这两个参数有且只有一个
    if (not work_order_id and not task_id) or (work_order_id and task_id): return HttpResponse('参数错误')
    user = request.user
    username = creator = user.username
    #只有order_id参数为添加工单
    if work_order_id: work_order_id = int(work_order_id)
    #只有id参数为编辑工单
    if task_id:
        task_id = int(task_id)
        ret = Task.objects.get(id=task_id)
        creator = ret.creator
        state = ret.state
        work_order_id = ret.work_order_id
        if creator != username: return HttpResponse('您不是本工单任务创建人')
        if state != 1: return HttpResponse('工单已处理')
        data = json.loads(ret.data)
        task_log = Task_log.objects.filter(task_id=task_id).order_by('-create_time')
    work_order_info = Work_order.objects.get(id=work_order_id)
    work_order_flow = work_order_info.flow
    if work_order_flow:
        next_role_id = int(work_order_flow.split('-')[0])
    else:
        next_role_id = 0
    work_order_title = work_order_info.title
    work_order_name = work_order_info.name
    #根据template_name名指定引用的form表单模板
    template_name = 'workflow/%s_form.html' % work_order_name
    display_submit = 1
    if next_role_id != 0:
        next_users = Role.objects.get(id=next_role_id).users.all()
    else:
        next_users = [user]
    role_dict = get_role_name()
    act_type_dict = settings.ACT_TYPE_DICT
    #工单form表单数据定义,新增工作流在此处添加表单数据
    if work_order_name == 'cicd':
        envs = ['deva', 'devb', 'devc', 'devd', 'deve', 'betaa', 'betab', 'betac', 'betad', 'grey', 'prod', 'android', 'ios']
    return render_to_response('workflow/add_task.html', locals())


@login_required
def show_task(request):
    title = '查看工单'
    #查看工单必须包含id参数
    task_id = request.GET.get('id','').strip()
    if not task_id: return HttpResponse('参数错误')
    task_id = int(task_id)
    ret = Task.objects.get(id=task_id)
    order_id = ret.work_order_id
    try:
        work_order_info = Work_order.objects.get(id=order_id)
    except:
        return HttpResponse('工作流不存在，无法查看工单')
    work_order_flow = ret.flow
    work_order_title = work_order_info.title
    work_order_name = work_order_info.name
    template_name = 'workflow/%s_form.html' % work_order_name
    creator = ret.creator
    data = json.loads(ret.data)
    user_info = User.objects.get(username=creator)
    creator_name = user_info.last_name
    creator_mail = user_info.email
    create_time = ret.create_time
    task_log = Task_log.objects.filter(task_id=task_id).order_by('-create_time')
    role_dict = get_role_name()
    act_type_dict = settings.ACT_TYPE_DICT
    #工单执行日志文件如果存在则显示执行日志
    log_file = '%s/logs/workflow/%d.log' % (settings.BASE_DIR, task_id)
    if os.path.exists(log_file):
        display_log = 1
        f = open(log_file)
        log = f.read()
        f.close()
        #查找日志文件中的关键字task_mark_percent判断工单执行进度百分比
        task_mark_percent_list = re.findall('task_mark_percent=(\d+)', log, re.M)
        task_mark_percent = 0
        if task_mark_percent_list: task_mark_percent = int(task_mark_percent_list[-1])
    return render_to_response('workflow/show_task.html',locals())

@login_required
def edit_task(request):
    title = '审批工单'
    #处理工单必须包含id参数
    task_id = request.GET.get('id','').strip()
    if not task_id: return HttpResponse('参数错误')
    task_id = int(task_id)
    user = request.user
    username = user.username
    is_supervisor = 0
    #判断是否有督办权限
    roles = [row.name for row in user.role_set.all()]
    if 'workflow_supervisor' in roles: is_supervisor = 1
    ret = Task.objects.get(id=task_id)
    cur_role_id = ret.cur_role_id
    state = ret.state
    if state == 0 or state == 1 or state == 5: return HttpResponse('工单已更新，流程已结束')
    order_id = ret.work_order_id
    work_order_info = Work_order.objects.get(id=order_id)
    work_order_title = work_order_info.title
    work_order_flow = ret.flow
    flow_list = work_order_flow.split('-')
    template_name = 'workflow/%s_form.html' % work_order_info.name
    cur_users = ret.cur_users
    cur_user = ret.cur_user
    #当前处理人是申请人和流程最后两个审批角色的人在页面中选择审批人隐藏
    if cur_role_id != 0 and flow_list.index(str(cur_role_id)) + 2 < len(flow_list): 
        display_users = 1
        next_role_id = flow_list[flow_list.index(str(cur_role_id))+1]
        next_users = Role.objects.get(id=next_role_id).users.all()
    #更新当前处理人
    if not cur_user and username in cur_users.split(';'):
        Task.objects.filter(id=task_id).update(cur_user=username)
        cur_user = username
    #判断是否处理工单权限
    cur_user_list = cur_users.split(';')
    if username in cur_user_list or is_supervisor == 1:
        creator = ret.title
        data = json.loads(ret.data)
        creator = ret.creator
        state = ret.state
        user_info = User.objects.get(username=creator)
        creator_name = user_info.last_name
        creator_mail = user_info.email
        create_time = ret.create_time
        task_log = Task_log.objects.filter(task_id=task_id).order_by('-create_time')
        role_dict = get_role_name()
        cur_act_type_dict = settings.ACT_TYPE_DICT
        #如果工单处理状态为申请人确认处理意见的选项只有确认和撤销
        if state == 4: cur_act_type_dict = settings.CREATOR_ACT_TYPE_DICT
        #工单执行日志文件如果存在则显示执行日志
        log_file = '%s/logs/workflow/%d' % (settings.BASE_DIR, task_id)
        if os.path.exists(log_file): 
            display_log = 1
            f = open(log_file)
            log = f.read()
            f.close()
            #查找日志文件中的关键字task_mark_percent判断工单执行进度百分比
            task_mark_percent_list = re.findall('task_mark_percent=(\d+)', log, re.M)
            task_mark_percent = 0 
            if task_mark_percent_list: task_mark_percent = int(task_mark_percent_list[-1])
        return render_to_response('workflow/edit_task.html',locals())
    else:
        return HttpResponse('工单状态已更新，您不是当前处理人')

@login_required
def ajax_get_log(request):
    #ajax刷新获取日志内容
    data = {}
    task_mark_percent = 0
    task_id = request.GET.get('id','').strip()
    if not task_id: 
        log = '获取日志的参数错误'
    else:
        task_id = int(task_id)
        log_file = '%s/logs/workflow/%d' % (settings.BASE_DIR, task_id)
        if os.path.exists(log_file):
            f = open(log_file)
            log = f.read()
            f.close()
            task_mark_percent = re.findall('task_mark_percent=(\d+)', log, re.M)[-1]
        else:
            log = '任务暂未执行,请稍等...'
    data['task_mark_percent'] = task_mark_percent
    data['log'] = log
    return HttpResponse(json.dumps(data))
