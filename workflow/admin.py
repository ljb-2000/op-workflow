#coding:utf-8
from django.contrib import admin
from .models import *

class Work_orderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'title', 'desc', 'creator', 'flow', 'is_active', 'take_time', 'create_time', 'update_time')

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'creator', 'work_order_id', 'flow', 'state', 'cur_role_id', 'cur_users', 'cur_user', 'create_time', 'update_time', 'data')

class Task_logAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_id', 'username', 'role_id', 'act_type', 'act_opinion', 'create_time')

admin.site.register(Work_order, Work_orderAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Task_log, Task_logAdmin)
