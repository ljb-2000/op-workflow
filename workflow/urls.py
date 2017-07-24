#coding:utf-8

from django.conf.urls import patterns, include, url
from .views import *

urlpatterns = [

    url(r'^$', order_list),
    url(r'^add_order/$', add_order, name='add_order'),
    url(r'^edit_order/$', edit_order, name='edit_order'),
    url(r'^ajax_order$', ajax_order, name='ajax_order'),
    url(r'^order_list/$', order_list, name='order_list'),
    url(r'^supervisor_task/$', supervisor_task, name='supervisor_task'),
    url(r'^waiting_task$', waiting_task, name='waiting_task'),
    url(r'^sent_task$', sent_task, name='sent_task'),
    url(r'^done_task$', done_task, name='done_task'),
    url(r'^del_task$', del_task, name='del_task'),
    url(r'^link_task/$', link_task, name='link_task'),
    url(r'^all_task/$', all_task, name='all_task'),
    url(r'^unlock_task/$', unlock_task, name='unlock_task'),
    url(r'^ajax_task$', ajax_task, name='ajax_task'),
    url(r'^add_task/$', add_task, name='add_task'),
    url(r'^show_task$', show_task, name='show_task'),
    url(r'^edit_task$', edit_task, name='edit_task'),
    url(r'^get_task_info$', get_task_info, name='get_task_info'),
    url(r'^ajax_get_log$', ajax_get_log, name='ajax_get_log'),
]
