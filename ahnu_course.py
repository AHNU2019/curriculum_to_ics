#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time : 2020/9/17 10:28
# @Author : 阿才
# @Site : https://hyacm.com
# @File : ahnu_course.py
# @Software: 记事本

import requests
from uuid import uuid1
import hashlib
import re
import math
import getpass
from icalendar import Calendar, Event    # pip install icalendar
from datetime import datetime,time
from datetime import timedelta
import json

DEBUG = False    # 调试模式，打印中间过程

start_date = datetime.strptime("2020-09-14", "%Y-%m-%d")		                # 开学日期
semester = 1    # 学期, 第一学期是前一半夏季作息时间, 第二学期是后一半夏季作息时间
winter_start_date = datetime.strptime("2020-11-2", "%Y-%m-%d")	                # 冬季作息表开始日期
winter_end_date = datetime.strptime("2021-4-4", "%Y-%m-%d")	                # 冬季作息表结束日期

url = "http://jw.ahnu.edu.cn/student/login"		# 安徽师范大学新教务系统地址
login_salt_url = "http://jw.ahnu.edu.cn/student/login-salt"        # 获取教务系统密码加盐url
checkurl = "http://jw.ahnu.edu.cn/student/login"        # 登录提交url
kcburl = "http://jw.ahnu.edu.cn/student/for-std/course-table/get-data?bizTypeId=2&semesterId=41"        # 课程表url

week = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6}


headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36",
    }

headers_content_json = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36",
        "Content-Type": "application/json",
    }    # json类型内容

headers_content_xml = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }    # xml request


# 定义课程类，方便管理课程信息
class Course(object):
    """课程类

    课程类

    """
    def __init__(self, name, start_week, end_week, day, start_time, end_time, school_area, room, teacher):
        """初始化Course

        初始化Course

        :param name: 课程名称
        :param start_week: 开始周
        :param end_week: 结束周
        :param day: 星期几
        :param start_time: 开始节数
        :param end_time: 结束节数
        :param school_area: 校区
        :param room: 教室
        :param teacher: 教师
        :return: 无返回
        """

        self.name = name
        self.start_week = start_week
        self.end_week = end_week
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.school_area = school_area
        self.room = room
        self.teacher = teacher

    def __str__(self):
        return '课程名称: {}, 第{}~{}周, 周{}, 第{}~{}节, 校区: {}, 教室: {}, 教师: {}.'.format(self.name,
            self.start_week, self.end_week, self.day, self.start_time, self.end_time, self.school_area,
            self.room, self.teacher )


def login(studentnumber, password):
    """登录

    登录，无返回值，在一个会话内执行可保持登录状态

    :param studentnumber: 用户名，学号
    :param password: 密码
    :return: 无返回
    """
    response = s.get(url, headers=headers)    # 模拟登录主页面
    DEBUG and print("login home page:", response.content.decode('utf-8'))

    login_salt = s.get(login_salt_url , headers=headers).content.decode('utf-8')    # 模拟获取密码加盐
    DEBUG and print("login salt:", login_salt)

    password_salt = login_salt + "-" + password    # 构造加盐后的密码
    password_post = hashlib.sha1(password_salt.encode('utf-8')).hexdigest()    # 模拟前端密码加密，使用sha1加密

    data = {"username": studentnumber,"password": password_post,"captcha":"","terminal":"student"}    # 模拟提交登录的用户名、加密的密码等
    DEBUG and print("post data: ", data)

    DEBUG and print("s headers: ", s.headers)

    print("学号: {}".format(studentnumber))
    response = s.post(checkurl, data=json.dumps(data), headers=headers_content_json).content.decode('utf-8')    # 提交登录
    DEBUG and print(response)
    
    # 尝试获取服务器异常，获取失败说明无异常
    try:
        print("exception", json.loads(response)["exception"])
        print("message", json.loads(response)["message"])
    except:    # 获取失败
        result = json.loads(response)
        if result.get("result", None):
            print("模拟登录成功")
        else:
            print("登录失败, message: {}".format(result.get("message", None)))
            exit(1)


def getLessons(savefile=None):
    """获取课程表课程

    从教务系统爬取课程表json数据，获取lessons。

    :param savefile: 保存课程表json文件的文件名，为空时不保存文件
    :return: 返回课程信息
    """
    kcb_page = s.get(kcburl , headers=headers_content_xml).content.decode('utf-8')    # 模拟访问课程表页面，默认就会显示当前学期的课程表
    DEBUG and print("kcb page: ", kcb_page)

    # 以json格式保存完整的教务系统课程表信息
    kcb_json = json.loads(kcb_page)
    if savefile:
        with open(savefile, 'w+', encoding='utf-8') as f:
            f.write(kcb_page)

    # DEBUG and print("kcb_json", kcb_json)
    DEBUG and print("type(kcb_json)", type(kcb_json))

    lessons = kcb_json.get('lessons', None)    # 解析 json课程表，获取课程信息

    return lessons


def praseLessons(lessons=None):
    """解析课程表

    解析lessons，将课程表转换为Course类

    :param lessons: 课程信息
    :return: 返回 Course 对象列表
    """
    courses = []    # 课程表列表，用来保存全部课程信息

    # 解析详细课程信息
    if lessons:
        for lesson in lessons:
            course = lesson.get('course')
            nameZh = course.get('nameZh')
            DEBUG and print(nameZh)
            scheduleText = lesson.get('scheduleText')
            dateTimePlacePersonText = scheduleText.get('dateTimePlacePersonText')
            infos = dateTimePlacePersonText.get('textZh')
            if infos:
                DEBUG and print(infos, type(infos))
                fulll_pattern = re.compile(r"\s*(\d+?)~(\d+?)周\s+周(.+?)\s+第?(.+?)节~第?(.+?)节\s+(.+?)\s+(.+?)\s+(.+?)(?:;|$)", re.U)
                res_kclist = fulll_pattern.findall(infos)
                DEBUG and print(res_kclist)
                no_room_pattern = re.compile(r"\s*(\d+?)~(\d+?)周\s+周(.+?)\s+第?(.+?)节~第?(.+?)节\s+([^\s]+?)(?:;|$)", re.U)
                no_room_res_kclist = no_room_pattern.findall(infos)
                for kc in no_room_res_kclist:
                    courses.append(Course( *((nameZh,) + kc[:5] + ("未安排校区", "未安排教室")  + kc[5:])) )
                for kc in res_kclist:
                    courses.append(Course( *((nameZh,) + kc)) )

    if DEBUG:
        for course in courses:
            print(course)

    return courses


# 上课时间, 每节课的起止时间
def get_course_time(start_time, end_time, summer=True):
    """获取作息时间

    根据是否为夏季返回作息时间，传参为每天的第几节到第几节。

    :param start_time: 开始节数
    :param end_time: 结束节数
    :param summer: 是否夏季，默认为True
    :return: 返回作息时间
    """
    if summer:
        sc = {'一': [[8, 0], [8, 45]],
             '二': [[8, 50], [9, 35]],
             '三': [[9, 50], [10, 35]],
             '四': [[10, 40], [11, 25]],
             '五': [[11, 30], [12, 15]],
             '六': [[14, 30], [15, 15]],
             '七': [[15, 20], [16, 5]],
             '八': [[16, 10], [16, 55]],
             '九': [[17, 10], [17, 55]],
             '十': [[18, 0], [18, 45]],
             '十一': [[19, 30], [20, 15]],
             '十二': [[20, 20], [21, 5]],
             '十三': [[21, 10], [21, 55]] 
            }
    else:
        sc = {'一': [[8, 0], [8, 45]],
             '二': [[8, 50], [9, 35]],
             '三': [[9, 50], [10, 35]],
             '四': [[10, 40], [11, 25]],
             '五': [[11, 30], [12, 15]],
             '六': [[14, 0], [14, 45]],
             '七': [[14, 50], [15, 35]],
             '八': [[15, 40], [16, 25]],
             '九': [[16, 40], [17, 25]],
             '十': [[17, 30], [18, 15]],
             '十一': [[19, 0], [19, 45]],
             '十二': [[19, 50], [20, 35]],
             '十三': [[20, 40], [21, 25]] 
            }

    return sc[start_time][0], sc[end_time][1]


def generateEvent(course, summer=False, count=17, start_date=start_date):
    """生成日历事件

    根据参数生成日历事件

    :param course: 课程信息
    :param summer: 夏季作息
    :param count: 事件重复次数，一般为周数
    :param start_date: 事件开始时间
    :return: 返回一个日历事件
    """
    event = Event()
    ev_start_date = start_date + timedelta(days=week[course.day])
    s_t, e_t = get_course_time(course.start_time, course.end_time, summer=summer)
    ev_start_datetime = datetime.combine(ev_start_date, time(s_t[0], s_t[1]))  
    ev_end_datetime = datetime.combine(ev_start_date, time(e_t[0], e_t[1]))
    ev_interval = 1

    event.add('uid', str(uuid1()) + '@AHNU')
    event.add('summary', course.name)
    event.add('dtstamp', datetime.now())
    event.add('dtstart', ev_start_datetime)
    event.add('dtend', ev_end_datetime)
    event.add('location', course.room)
    event.add('rrule', {'freq': 'weekly', 'interval': ev_interval, 'count': count})
    event.add('comment', "教师:" + course.teacher)

    return event


def to_ics(courses, savefile="kcb.ics"):
    """转换为日历

    将课程表转换为日历文件

    :param courses: Course课程列表
    :param savefile: 保存日历文件路径
    :return: 无返回
    """
    print("正在生成日历……")
    global start_date
    if start_date.weekday() != 0:
        ee = timedelta(days=start_date.weekday())
        start_date_first_day = start_date - ee
    else:
        start_date_first_day = start_date
    cal = Calendar()
    cal['version'] = '2.0'
    cal['prodid'] = '-//AHNU//阿才//CN'
    for course in courses:
        start_date_first_week = start_date_first_day + timedelta(days=7*(int(course.start_week)-1))
        all_weeks = int(course.end_week) - int(course.start_week) + 1
        if semester == 1:
            days_delta = winter_start_date - start_date_first_week
            first_weeks = math.ceil(days_delta.days / 7)
            last_weeks = all_weeks - first_weeks
            first_event = generateEvent(course, summer=True, count=first_weeks, start_date=start_date_first_week)
            last_event = generateEvent(course, summer=False, count=last_weeks, start_date=winter_start_date)
        elif semester == 2:
            days_delta = winter_end_date - start_date_first_week
            first_weeks = math.ceil(days_delta.days / 7)
            last_weeks = all_weeks - first_weeks
            first_event = generateEvent(course, summer=False, count=first_weeks, start_date=start_date_first_week)
            last_event = generateEvent(course, summer=True, count=last_weeks, start_date=winter_end_date)
        else:
            print("not implement")
        
        cal.add_component(first_event)
        cal.add_component(last_event)

    with open(savefile, 'w+', encoding='utf-8') as file:
        ical = cal.to_ical().decode('utf-8')
        file.write(cal.to_ical().decode('utf-8').replace('\r\n', '\n').strip())
    print("已将所有课程生成日历文件: {}".format(savefile))


if __name__ == "__main__":
    studentnumber = input("学号: ")
    password = getpass.getpass("密码(已隐藏,输入时无提示): ")
    s = requests.session()    # 开始一个会话，在会话内进行操作，可以保持登录状态
    login(studentnumber, password)    # 登录
    lessons = getLessons(savefile='kcb_raw.json')    # 获取lessons
    courses = praseLessons(lessons=lessons)    # 解析lessons
    to_ics(courses=courses)    # 转换为日历文件
     


