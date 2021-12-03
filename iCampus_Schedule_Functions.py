from datetime import datetime, timedelta
import time
from time import strftime, gmtime
from pytz import timezone
from tkinter import *
from tkinter import font
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import json
import requests
import threading
from math import ceil
from copy import deepcopy
from random import random

############## Functions (modify time data in json files) ##########################
# modify time data in json files.
def str_to_time(str):
    time = datetime.fromisoformat(str[:-1])
    return time
def utc_to_kst(utc_time):
    kst_time = utc_time + timedelta(hours = 9)
    return kst_time
def str_to_kst(str):
    utc_time = str_to_time(str)
    kst_time = utc_to_kst(utc_time)
    return kst_time

def datetime_info(week_num, day_num, type):    # return date objects # type = (datetime, weekday) # week_num // now week == 0 # day_num // mon == 0
    datetime_now_kr = datetime.now(tz=timezone('Asia/Seoul'))
    datetime_info = datetime_now_kr + timedelta(weeks=week_num, days=day_num - datetime_now_kr.weekday())
    if type == 'datetime':
        datetime_info = datetime_info.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        return datetime_info
    elif type == 'date':
        date_info = datetime_info.date()
        return date_info
    elif type == 'weekday':
        day_list = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        weekday = datetime_info.weekday()
        day = day_list[weekday]
        return day

def datetime_to_index(datetime):
    datetime_index = list()
    mon = datetime_info(0, 0, 'date')
    date_diff = datetime.date() - mon
    week_num, day_num = divmod(date_diff.days, 7)
    time_diff = datetime - datetime.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    a, b = divmod(time_diff.seconds, 1800)
    if a < 16:
        time_num = 0
    else:
        time_num = a - 16
        if b != 0:
            time_num += 1
    datetime_index = [week_num, day_num, time_num]
    return datetime_index

def available_time_index(start, end):
    remove_list = [67,100,133,166,199,232]
    index_list = list(range(start, end+1))
    for num in remove_list:
        try:
            index_list.remove(num)
        except:
            pass
    return index_list

def week_info(week_num):    # week_num <- integer, 1 == next_week, 0 == current_week, # type == str, sun 
        mon = datetime_info(week_num, 0, 'date')
        sun = datetime_info(week_num, 6, 'date')
        mon_str = mon.strftime("%Y / %m / %d")
        sun_str = sun.strftime("%Y / %m / %d")
        week_info = f'{mon_str}\n{sun_str}'
        return week_info

def check_timetable_date(now, timetable_0):
    if now.weekday() == 0:
        # 새로운 주가 되면 파이썬 새로 실행
        pass
    else:
        timetable_0.highlight_today()

def cell_needed(duration):
        q, r = divmod(duration, 1800)
        if r == 0:
            return q
        else:
            return q + 1

def random_int(n):
    a = random()*(10**n)
    return int(a)

def coordinate(button_index, x, y):   # 112, 169, 24
    q, r = divmod(button_index-1, 33)
    if q == 0:
        x_axis = 0 + x
        y_axis = 24*r + y
    else:
        x_axis = 113 + 169*(q-1) + x
        y_axis = 24*r + y
    if q == 7:
        x_axis -= 148
    if r >= 27:
        y_axis -= 116
    return x_axis, y_axis

###############################################################################################
class timetable():
    def setTimetable(self, frame, label_selected_cell):    # initial settings
        self.label_selected_cell = label_selected_cell
        self.font = font.Font(family='Arial', size=7)
        self.clicked_buttons = list()
        self.flicker_button_status = [False, None, None, None]    # [status, widget, index, button['background']]
        self.table_cell = [None]
        self.frame = frame
        self.set_colors()
        self.make_timetable_widget(frame)

    def set_colors(self):
        self.color_selected = '#DBDCE1'
        self.color_not_selected = '#FFFFFF'
        self.color_lecture = '#BCBDC6'
        self.color_day = '#657EA1'

    def make_timetable_widget(self, frame):
        # makes time table, # column = 8, row = 33 # frame 안에 button(cell) 배열
        for column in range(8):
            for row in range(33):
                self.table_cell.append(f'cell_{row}_{column}')
                index, text = self.cell_info(row, column)
                if column == 0:
                    self.table_cell[index] = Button(frame, text=text, background=self.color_not_selected, relief='ridge', borderwidth=1, width=15, height=1)
                    self.table_cell[index].bind('<Button-1>', self.place_forget_cellInfoLabel)
                    self.table_cell[index].bind('<Button-3>', self.place_forget_cellInfoLabel)
                elif column != 0 and row == 0:
                    self.table_cell[index] = Button(frame, text=text, background=self.color_not_selected, relief='ridge', borderwidth=1, width=23, height=1)
                    self.table_cell[index].bind('<Button-1>', self.place_forget_cellInfoLabel)
                    self.table_cell[index].bind('<Button-3>', self.place_forget_cellInfoLabel)
                else:    # click 함수가 필요한 buttons 만 함수에 연결
                    self.table_cell[index] = Button(frame, text=text, background=self.color_not_selected, relief='ridge', borderwidth=1, width=23, height=1)
                    self.table_cell[index].bind('<Button-1>', self.left_click)    # mouse_left_click           # => single select
                    self.table_cell[index].bind('<Shift-1>', self.shift_click)    # <shift> + mouse_left_click # => drag select
                    self.table_cell[index].bind('<Button-3>', self.right_click)   # mouse_right_click          # => show cell info
                self.table_cell[index].grid(row=row, column=column)    # button을 grid에 배치

    def cell_info(self, row, column):    # cell(button)의 역할 구분 and 'text' 배정
        index = (row) + (column*33) + 1
        text = ''
        if column == 0 and row > 0:    # (0,i), i=1, ...,33 # time cells(buttons)
            seconds = 27000 + 1800 * row
            text = strftime('%H : %M', gmtime(seconds))
        elif row == 0:
            day_list = ['', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            text = day_list[column]
        self.day_index = [34, 67, 100, 133, 166, 199, 232]    # index of buttons in day_list
        return index, text

    def left_click(self, event):    # (left_click) 을 눌렀을 때 cell 하이라이트
        button_name = str(event.widget)
        index = int(button_name[button_name.index('button')+6:])
        global button
        if self.flicker_button_status[0] == True:
            self.multi_select_end(index)
        else:
            button_name = str(event.widget)
            index = int(button_name[button_name.index('button')+6:])
            self.change_color(event.widget, index)

    def shift_click(self, event):    # (shift) + (left_click) # 다중선택.
        button_name = str(event.widget)
        index = int(button_name[button_name.index('button')+6:])
        global button
        if self.flicker_button_status[0] == False:    # multiple select not active; start multi_select
            self.multi_select_start(event, index)
        else:                 # multiple select active; terminate multi_select
            self.multi_select_end(index)

    def place_forget_cellInfoLabel(self, event):
        try:
            self.label_cell_info.place_forget()
        except:
            pass

    def right_click(self, event):    # (left_click), 만약 cell 에 강의 정보가 있다면 더 자세한 강의 정보 보여줌
        try:
            self.label_cell_info.place_forget()
        except:
            pass
        widget_text = event.widget['text']
        if widget_text == '':
            return
        else:
            lecture_button = list()
            lecture_name_list = widget_text.split(', ')
            for lecture_name in lecture_name_list:
                for lecture in self.lecture_list:
                    if lecture_name == lecture.title():
                        lecture_button.append(lecture)
        widget_name = str(event.widget)
        widget_index = int(widget_name[widget_name.find('button') + 6:])
        x_axis, y_axis = coordinate(widget_index, event.x, event.y)
        label_text = ''
        for i, lecture in enumerate(lecture_button):
            text = f'{i}. {lecture.title()}\nduration: {lecture.duration_cl()}\ndue: {lecture.due_kst_ul()}\n'
            label_text += text
        self.label_cell_info = Label(self.frame,width=24, height=8, font=self.font, text=label_text, justify='left', background='#FFFFFF',relief="solid",bd=1)
        self.label_cell_info.bind('<Button-1>', self.place_forget_cellInfoLabel)
        self.label_cell_info.bind('<Button-3>', self.place_forget_cellInfoLabel)
        self.label_cell_info.place(x=x_axis, y=y_axis)
        self.label_cell_info.lift()

    def multi_select_start(self, event, index):    # (shift + left_click) 다중 선택 시작. 버튼 깜빡임 시작.
        self.flicker_button_status[0] = True
        self.flicker_button_status[1] = event.widget
        self.flicker_button_status[2] = index
        self.flicker_button_status[3] = event.widget['background']
        self.flicker_button()

    def multi_select_end(self, index):    # (shift + left_click) 다중 선택 종료. 버튼 깜빡임 종료.
        self.flicker_button_status[0] = False
        if self.flicker_button_status[3] == self.color_not_selected:
            self.table_cell[self.flicker_button_status[2]]['background'] = self.color_not_selected
        else:
            self.table_cell[self.flicker_button_status[2]]['background'] = self.color_selected
        if self.flicker_button_status[2] <= index:
            for i in range(self.flicker_button_status[2], index+1):
                if not i in self.day_index:
                    self.change_color(self.table_cell[i], i)
        else:
            for i in range(index, self.flicker_button_status[2]+1):
                if not i in self.day_index:
                    self.change_color(self.table_cell[i], i)
        self.flicker_button_status[2] = None
        self.flicker_button_status[3] = None

    def flicker_button(self):    # 버튼 깜빡임 함수
        if self.flicker_button_status[0] == True:
            if self.flicker_button_status[1]['background'] == self.color_not_selected:
                self.flicker_button_status[1]['background'] = self.color_selected
            else:
                self.flicker_button_status[1]['background'] = self.color_not_selected
            threading.Timer(0.4, self.flicker_button).start()
        else:
            pass

    def change_color(self, widget, index):    # change color of widget[index]
        try:
            if widget['background'] == self.color_not_selected:
                widget['background'] = self.color_selected
                self.clicked_buttons.append(index)
            else:
                widget['background'] = self.color_not_selected
                self.clicked_buttons.remove(index)
            self.change_label_selected_cell()
        except:
            print(f'!!!!errors!!!! widget={widget}, index={index}')

    def change_label_selected_cell(self):
        self.label_selected_cell.configure(text=f'selected cells: {len(self.clicked_buttons)}')

    def highlight_today(self):
        for index in self.day_index:
            self.table_cell[index]['background'] = self.color_not_selected
        today = datetime.today().weekday()    # mon = 0, tue = 1, ..., sun = 6
        today_index = 33*(today+1)+1
        self.table_cell[today_index]['background'] = self.color_day
    
    def append_lecture_list(self, lecture_list):
        self.lecture_list = lecture_list

class iCampus:
    def __init__(self, driver):
        self.driver = driver

    def login(self, id, pw):    # login # open login page, send keys
        self.driver.get("https://icampus.skku.edu/login")
        self.driver.implicitly_wait(5)
        self.driver.find_element_by_id("userid").send_keys(id)
        self.driver.find_element_by_id("password").send_keys(pw)
        self.driver.find_element_by_id("btnLogin").click()
        self.driver.implicitly_wait(5)
        time.sleep(0.4)
        try:
            WebDriverWait(self.driver, 2).until(expected_conditions.alert_is_present())    # alert = login not successful
            alert = self.driver.switch_to.alert
            alert.dismiss()
            return False
        except:    # login success
            return True

    def get_courses(self):    # api 에서 강의 정보를 json 으로 가져옴
        self.driver.get("https://canvas.skku.edu/api/v1/users/self/favorites/courses")
        self.driver.implicitly_wait(5)
        element = self.driver.find_element_by_xpath('/html/body/pre')
        element_text = element.text
        index = element_text.find(';')
        self.courses_json = json.loads(element_text[index+1:])

    def get_id(self):
        self.random_course_id = str(self.courses_json[0]['id'])
        self.user_id = str(self.courses_json[0]['enrollments'][0]['user_id'])

    def get_token(self):
        # canvas.skku.edu 와의 연결에 필요한 토큰 가져오기. 
        # token 가져오는 부분 출처: https://github.com/ductility/iCampusCheck, ductility, Icampus Check(아캠체크)
        self.driver.get("https://canvas.skku.edu/courses/" + str(self.random_course_id) + "/external_tools/5")
        self.driver.implicitly_wait(5)
        time.sleep(0.5)
        while True:
            print('try getting xn_api_token')
            ### **출처 아캠체크** ##
            token = self.driver.execute_script("var value = document.cookie.match('(^|;) ?' + 'xn_api_token' + '=([^;]*)(;|$)'); return value? value[2] : null;")
            ###
            if token == None:
                time.sleep(0.5)
            else:
                break
        self.xn_api_token = 'Bearer ' + token

    def get_student_info(self):    # 사용자 이름, 학번 가져오기
        user_info = requests.get("https://canvas.skku.edu/learningx/api/v1/courses/" + str(self.random_course_id) + "/total_learnstatus/users/" + str(self.user_id), headers = {"Authorization": self.xn_api_token})
        user_info_json = user_info.json()
        user_name = user_info_json['item']['user_name']
        index = user_name.find('(')
        self.user_name = user_name[:index]
        self.student_id = str(user_info_json['item']['user_login'])

    def get_json(self):    # 개별 강의 안의 정보 가져온다. json -> dict
        start = time.time()
        self.courses_dict = dict()
        courses_lecture_dict = list()
        for course_json in self.courses_json:
            course_name = course_json['name']
            course_id = str(course_json['id'])
            self.courses_dict[course_name] = course_id    # get (name) and (id) of all courses
            req = requests.get("https://canvas.skku.edu/learningx/api/v1/courses/" + course_id + "/sections/learnstatus_db?user_id=" + self.user_id + "&user_login=" + self.student_id + "&role=1", headers = {"Authorization": self.xn_api_token})
            course = courseInfo()
            course.set_data(req.json())
            required_components_list = course.get_required_components()
            if required_components_list == []:
                continue
            for component in required_components_list:
                component['course_name'] = course_json['name']
                component['course_id'] = str(course_json['id'])
                courses_lecture_dict.append(component)
            # courses_lecture_dict.append({'name': course_json['name'], 'id': str(course_json['id']), 'lectures': required_components_list})
        print("time :", time.time() - start)
        return courses_lecture_dict

class courseInfo:
    def set_data(self, json):
        self.course_sections = json['sections']
        self.components_list = self.get_all_components()

    def get_all_components(self):    # finding all components in (courses-lectures) # bottom up
        components_list = list()
        for sections in self.course_sections:
            for subsections in sections['subsections']:
                for units in subsections['units']:
                    for components in units['components']:
                        components_list.append(components)
        return components_list

    def get_required_components(self):
        # 조건에 맞는 강의만 골라낸다. 현재 < 강의 마감 < 다음주 일요일 23:59:59
        datetime_end_kr = datetime_info(2,0,'datetime')
        datetime_end_utc = datetime_end_kr - timedelta(hours=9)
        datetime_now_utc = datetime.utcnow()
        required_components_list = list()
        for component in self.components_list:
            try:
                if component['completed'] != False:
                    continue
                # component_type = ['movie', 'file', 'discussion', 'pdf', 'text', 'quiz', 'assignment']
                # {component | component is in ['movie', 'quiz', 'assignment']}
                if component['type'] != 'movie' and component['type'] != 'quiz' and component['type'] != 'assignment':
                    continue
                datetime_due_utc = str_to_time(component['due_at'])          # component['due_at'] -> YYYY-MM-DDTHH-MM-SSZ -> delete Z
                if datetime_now_utc and datetime_now_utc <= datetime_due_utc and datetime_due_utc < datetime_end_utc:    # unlock <= now <= due <= (end of the second week)
                    required_components_list.append(component)
                continue
            except:
                #print(component)
                pass
        return required_components_list

class lecture_info:    # 강의 정보
    def __init__(self, lecture):
        self.lecture = lecture
    # cl = click_lecture, ul = update_lectures
    def course_name_cl(self):
        course_name = self.lecture['course_name']
        return course_name
    def course_name_ul(self):
        name = self.lecture['course_name']
        course_name = name[:name.find('_')]
        return course_name
    def title(self):
        title = self.lecture['title']
        return title
    def unlock_kst_cl(self):
        unlock_at = str_to_kst(self.lecture['unlock_at']).strftime('%Y-%m-%d T %H:%M:%S')
        return unlock_at
    def due_kst_cl(self):
        due_at = str_to_kst(self.lecture['due_at']).strftime('%Y-%m-%d T %H:%M:%S')
        return due_at
    def due_kst_ul(self):
        due_at = str_to_kst(self.lecture['due_at']).strftime('%b %d')
        return due_at
    def lecture_type(self):
        lecture_type = self.lecture['type']
        return lecture_type
    def id(self):
        lecture_id = self.lecture['component_id']
        return lecture_id
    def duration_cl(self):
        try:
            time = timedelta(seconds = ceil(self.lecture['commons_content']['duration']))
        except:
            time = 'None'
        return time
    def duration(self):
        try:
            time = ceil(self.lecture['commons_content']['duration'])
        except:
            time = None
        return time

    def get_available_time(self):
        # unlock 시간과 now 를 비교해 더 뒤에 있는 시간을 시작 시간으로 설정
        # due 를 끝시간으로 설정
        # 시작시간과 끝시간 사이에 있는 시간을 (가능시간)으로 설정.
        self.available_time_list = [[],[]]
        datetime_now_kr = datetime.now()
        unlock = str_to_kst(self.lecture['unlock_at'])
        due = str_to_kst(self.lecture['due_at'])
        if unlock < datetime_now_kr:
            start_index = datetime_to_index(datetime_now_kr)
        else:
            start_index = datetime_to_index(unlock)
        due_index = datetime_to_index(due)
        start = 35+(33*start_index[1])+start_index[2]
        end = 35+(33*due_index[1])+due_index[2]
        if start_index[0] == 0 and due_index[0] == 0:
            index = available_time_index(start, end)
            self.available_time_list[0].extend(index)
        elif start_index[0] == 0 and due_index[0] == 1:
            index_0 = available_time_index(start, 264)
            index_1 = available_time_index(35, end)
            self.available_time_list[0].extend(index_0)
            self.available_time_list[1].extend(index_1)
        else:    # start_index[0] == 1 and due_index == 1:
            index = available_time_index(start, end)
            self.available_time_list[1].extend(index)

    def get_selected_available_time(self, selected_time):
        # (가능시간) 중 사용자가 선택한 시간과 겹치는 시간을 얻음. = 가용시간
        set_selected_time_0 = set(selected_time[0])
        set_available_time_0 = set(self.available_time_list[0])
        set_selected_time_1 = set(selected_time[1])
        set_available_time_1 = set(self.available_time_list[1])
        selected_available_time_0 = list(set_selected_time_0 & set_available_time_0)
        selected_available_time_1 = list(set_selected_time_1 & set_available_time_1)
        self.selected_available_time = [selected_available_time_0, selected_available_time_1]

    def get_contiguous_index(self):
        # 가용시간에서 강의시간이 들어갈 수 있는 모든 시간 index 를 구함
            self.con_index = [[],[]]
            for i in self.selected_available_time[0]:
                error = 0
                for j in range(i+1, i+self.cell_n):
                    if j not in self.selected_available_time[0]:
                        error+=1
                        break 
                if error == 0:
                    self.con_index[0].append(list(range(i,i+self.cell_n)))
            for i in self.selected_available_time[1]:
                error = 0
                for j in range(i+1, i+self.cell_n+1):
                    if j not in self.selected_available_time[1]:
                        error+=1
                        break
                if error == 0:
                    self.con_index[1].append(list(range(i,i+self.cell_n)))

    def final_time_list(self, selected_time):
        # get_available_time, get_selected_available_time, get_contiguous_index 를 통해 얻은 가용 시간
        # 가용시간이 timetable 에 들어갈 수 있는 모든 경우의 수를 구한다.
        self.get_available_time()
        self.get_selected_available_time(selected_time)
        self.cell_n = cell_needed(self.duration())
        self.get_contiguous_index()
        index_list = [[],[]]
        r = self.duration() % 1800
        if r == 0:
            for i, week in enumerate(self.con_index):
                for l in week:
                    new_list = list()
                    for index in l:
                        new_list.append([index,1800])
                    index_list[i].append(new_list)
            return index_list
        if self.cell_n == 1:
            for i, week in enumerate(self.con_index):
                for l in week:
                    new_list = list()
                    new_list.append([l[0],r])
                    index_list[i].append(new_list)
            return index_list
        elif self.cell_n == 2:
            for i, week in enumerate(self.con_index):
                for l in week:
                    new_list = list()
                    new_list.append([l[0],1800])
                    new_list.append([l[1],r])
                    index_list[i].append(new_list)
                    new_list = list()
                    new_list.append([l[0],r])
                    new_list.append([l[1],1800])
                    index_list[i].append(new_list)
            return index_list
        else:
            for i, week in enumerate(self.con_index):
                for l in week:
                    new_list = list()
                    for j in range(self.cell_n):
                        if j == self.cell_n-1:
                            new_list.append([l[-1],r])
                            continue
                        new_list.append([l[j],1800])
                    index_list[i].append(new_list)
                    new_list = list()
                    for j in range(self.cell_n):
                        if j == 0:
                            new_list.append([l[0],r])
                            continue
                        new_list.append([l[j],1800])
                    index_list[i].append(new_list)
            return index_list

class timeMatrix():
    # 이전에 얻은 (가용시간)을 고려해 시간표에 1번 강의 부터 넣음.
    # 강의마다 가능한 경우의 수 2가지를 얻고, 2가지 중 최선의 경우(최대한 cell을 적게 차지하는 경우) 만 남기고 나머지는 삭제.
    # 하나하나 강의를 비교하여 최적의 경우 구함.
    def __init__(self):
        self.set_vars()

    def set_vars(self):
        self.total_cases = list()
        self.num_first_lectures = 0
        self.how_many = 0

    def make_matrix(self):
        matrix = [[None for col in range(0,265)] for row in range(2)]
        days = [34, 67, 100, 133, 166, 199, 232]
        for i in range(34):
            matrix[0][i] = False
            matrix[1][i] = False
        for i in days:
            matrix[0][i] = False
            matrix[1][i] = False
        return matrix

    def append_lecture(self, n_lecture, l_t_index):
        self.lt_index = l_t_index
        self.n_lecture = n_lecture
        if self.total_cases == []:
            self.append_first_lecture()
            return True
        else:
            if self.append_add_lecture():
                return True
            else:
                return False

    def append_first_lecture(self):
        self.first_list = list()
        org_matrix = self.make_matrix()
        for n_week, week in enumerate(self.lt_index):
            for con_index in week:
                if self.num_first_lectures == 1:
                    break
                matrix = deepcopy(org_matrix)
                self.append_first_matrix(matrix, n_week, con_index)
                self.num_first_lectures += 1
        self.total_cases.append(self.first_list)

    def append_first_matrix(self, matrix, n_week, con_index):
        for cell in con_index:
            index = cell[0]
            duration = cell[1]
            matrix[n_week][index] = [[self.n_lecture], [duration]]
        self.first_list.append(matrix)

    def append_add_lecture(self):
        self.add_list = list()
        self.num_lectures = 0
        for i, first_matrix in enumerate(self.total_cases[-1]):
            for n_week, week in enumerate(self.lt_index):
                for con_index in week:
                    self.how_many += 1
                    if self.num_lectures == 2:
                        break
                    matrix = deepcopy(first_matrix)
                    self.append_add_matrix(matrix, n_week, con_index)
        if len(self.add_list) == 2:
            list1 = 0
            list2 = 0
            for week in self.add_list[0]:
                for i in week:
                    if i != None and i != False:
                        list1 += 1
            for week in self.add_list[1]:
                for i in week:
                    if i != None and i != False:
                        list2 += 1
            if list1 < list2:
                del self.add_list[1]
            elif list1 > list2:
                del self.add_list[0]
            else: # list1 = list2:
                del self.add_list[1]
        elif len(self.add_list) == 0:
            return False
        self.total_cases.append(self.add_list)
        return True

    def append_add_matrix(self, matrix, n_week, con_index):
        len_con_index = len(con_index)
        start_index = 0
        end_index = len_con_index-1
        overlap_start = False
        overlap_end = False
        n = 0
        for cell in con_index:
            index = cell[0]
            duration = cell[1]
            if matrix[n_week][index] == None:
                n += 1
            else:
                if index == start_index:
                    if sum(matrix[n_week][index][1])+duration <= 1800:
                        n += 1
                        overlap_start = True
                    else:
                        return
                elif index == end_index:
                    if sum(matrix[n_week][index][1])+duration <= 1800:
                        n += 1
                        overlap_end = True
                    else:
                        return
                else:
                    return
                    
        if n == len_con_index:
            for cell in con_index:
                index = cell[0]
                duration = cell[1]
                if index == start_index:
                    if overlap_start:
                        matrix[n_week][index][0].append(self.n_lecture)
                        matrix[n_week][index][1].append(duration)
                        continue
                if index == end_index:
                    if overlap_end:
                        matrix[n_week][index][0].append(self.n_lecture)
                        matrix[n_week][index][1].append(duration)
                        continue
                matrix[n_week][index] = [[self.n_lecture],[duration]]
            self.num_lectures += 1
            self.add_list.append(matrix)
        else:
            print('line 519:')

    def get_opt_matrix(self):
        print(self.how_many)
        return self.total_cases[-1][0]