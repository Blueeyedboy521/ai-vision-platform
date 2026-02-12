# -*- coding: utf-8 -*-
"""
告警消费者模块

提供告警处理的后台线程池
"""
from .worker_pool import AlarmWorkerPool, alarm_worker_pool
from .alarm_consumer import process_alarm

__all__ = ["AlarmWorkerPool", "alarm_worker_pool", "process_alarm"]
