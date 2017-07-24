#coding:utf-8

from django.db import models
from django.contrib.auth.models import User

class Role(models.Model):
    name = models.CharField('角色名', max_length=50, unique=True)
    zh_name = models.CharField('角色中文名', max_length=100)
    desc = models.CharField('角色权限说明', max_length=500, blank=True)
    creator = models.CharField(u'创建人',max_length=30, blank=True)
    users = models.ManyToManyField(User)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

