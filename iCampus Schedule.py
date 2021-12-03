from re import L
from tkinter import *
from tkinter import font, ttk, messagebox
from tkcalendar import *
from time import strftime
import os
from selenium import webdriver
import pickle
from datetime import datetime, timedelta
import chromedriver_autoinstaller
from iCampus_Schedule_Functions import iCampus, timetable, lecture_info, timeMatrix, week_info, check_timetable_date, datetime_info, cell_needed, random_int

def check_chrome_version():    
    # before running program, check (chrome,chromedriver) version
    # if (chromedriver is not installed) or (chromedriver version != chrome version): install suitable chromedriver
    # ask the user if they want to install the new version. if not agree: notice program will not work
    global chromedriver_directory
    current_chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]  # get current (chrome version)
    with open(os.path.join(pickle_directory, 'data.p'), 'rb') as file:    # './data/data.p' = import initial data
        chrome_ver = pickle.load(file)
    if current_chrome_ver == chrome_ver:
        chromedriver_directory = os.path.join(program_directory, chrome_ver)
        return
    else:
        ask = messagebox.askokcancel('Warning', "The chromedriver version does not match.\nClick 'ok' to download newest version.", icon='warning')
        if ask:
            pass
        else:
            return
    try:
        driver = webdriver.Chrome(f'./{current_chrome_ver}/chromedriver.exe', options=options)   
    except:
        chromedriver_autoinstaller.install(True)
        driver = webdriver.Chrome(f'./{current_chrome_ver}/chromedriver.exe', options=options)
    driver.implicitly_wait(10)
    chrome_ver = current_chrome_ver
    chromedriver_directory = os.path.join(program_directory, chrome_ver)
    with open(os.path.join(pickle_directory, 'data.p'), 'wb') as file:
        pickle.dump(chrome_ver, file)
    driver.close()
    messagebox.showinfo('Download succes', "Now the chromedriver is now up to date!")

class Application(Frame):    # Main Window
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title('Schedule')
        self.master.geometry("1650x950+0+0")    # window size, geometry((width)x(height)+(x-axis)+(y-axis))
        self.pack()
        # initial settings
        check_chrome_version()
        self.set_vars()
        self.set_fonts()
        self.create_widgets()
        self.update_clock()

    def set_vars(self):
        self.login_status = False
        self.settings_status = False
        self.settings_update_status = False
        self.lectures_list = list()
        self.today = datetime.today()

    def set_fonts(self):
        self.title_font = font.Font(family='Arial', size=16, weight="bold")
        self.button_login_font = font.Font(family='Arial', size=10)

    def create_widgets(self):
        ## title
        self.label_title = Label(self.master, text='iCampus Schedule', font=self.title_font)
        self.label_title.bind('<Enter>', self.change_label_title)
        self.label_title.bind('<Leave>', self.change_label_title)
        self.label_title.place(relx=0.01, rely=0.01)

        ## Frame - login (info, button)
        self.frame_login = Frame(self.master, relief="sunken", bd=1, padx=0, pady=0)
        self.frame_login.place(relx=0.01, rely=0.05)
        # - info # displays (student name, student id)
        self.listBox_info = Listbox(self.frame_login, width=20, height=2)
        self.listBox_info.grid(row=0, column=0)
        self.listBox_info.insert(0, 'Student Name')
        self.listBox_info.insert(1, 'Student Id')
        # - login button # connected to (Login Window)
        self.button_login = Button(self.frame_login, text='Login', relief='raised', cursor='hand2', width=5, height=2, font=self.button_login_font, command=self.open_loginWindow)
        self.button_login.grid(row=0, column=1)

        ## Frame - course_info (info, button)
        self.frame_courseInfo = Frame(self.master, relief="sunken", bd=1, padx=0, pady=0)
        self.frame_courseInfo.place(relx=0.01, rely=0.1)
        # - courses
        self.treeView_courses = ttk.Treeview(self.frame_courseInfo, height=20, selectmode='none', columns=['1', '2', '3', '4'], displaycolumns=['1', '2', '3', '4'])
        self.treeView_courses.column('#0', width=35)
        self.treeView_courses.heading('#0', text='#')
        self.treeView_courses.column('#1', width=86)
        self.treeView_courses.heading('#1', text='course')
        self.treeView_courses.column('#2', width=105)
        self.treeView_courses.heading('#2', text='lecture')
        self.treeView_courses.column('#3', width=71)
        self.treeView_courses.heading('#3', text='duration')
        self.treeView_courses.column('#4', width=135)
        self.treeView_courses.heading('#4', text='id')
        self.treeView_courses['displaycolumns'] = ['1','2','3']
        self.treeView_courses.pack(anchor='n')
        # - setting button
        self.button_settings = Button(self.frame_courseInfo, text='settings', cursor='hand2', width=35, height=4, font=self.button_login_font, command=self.open_settingsWindow)
        self.button_settings.pack(anchor='se', pady=10)

        ## timetable
        # label selected cell number
        self.label_selected_cell = Label(self.master, text='selected cells: 0', bd=20)
        self.label_selected_cell.place(relx=0.01,rely=0.9)
        # label needed cell number
        self.label_needed_cell = Label(self.master, text='needed cells: 0', bd=20)
        self.label_needed_cell.place(relx=0.01,rely=0.8)
        # label
        self.label_left_click = Label(self.master, text='<left click>: select cell', bd=20)
        self.label_shift_click = Label(self.master, text='<shift> + <left click>: multi select', bd=20)
        self.label_right_click = Label(self.master, text='<right click>: show cell info', bd=20)
        self.label_left_click.place(relx=0.63,rely=0.94)
        self.label_shift_click.place(relx=0.72,rely=0.94)
        self.label_right_click.place(relx=0.85,rely=0.94)
        # - table 1 # current week
        self.frame_timetable = Frame(self.master, relief="solid", bd=1, padx=0, pady=0)
        self.timetable_0 = timetable()
        self.timetable_0.setTimetable(self.frame_timetable, self.label_selected_cell)
        self.timetable_0.highlight_today()
        self.frame_timetable.place(relx=0.2, rely=0.1)
        # - table 2 # next week
        self.frame_timetable_2 = Frame(self.master, relief="solid", bd=1, padx=0, pady=0)
        self.timetable_1 = timetable()
        self.timetable_1.setTimetable(self.frame_timetable_2, self.label_selected_cell)
        # - switch button # switches timetable
        self.button_next = Button(self.master, text='>', cursor='hand2', width=5, height=1, font=self.button_login_font, command=lambda current_week=0 : self.switch_timetable(current_week))
        self.button_next.place(relx=0.955, rely=0.06)
        self.button_prev = Button(self.master, text='<', cursor='hand2', width=5, height=1, font=self.button_login_font, command=lambda current_week=1 : self.switch_timetable(current_week))
        self.button_prev.place(relx=0.865, rely=0.06)
        self.message_week = Message(self.master, text=week_info(0), width=200, relief='solid')
        self.message_week.place(relx=0.9, rely=0.05)
        # clock
        self.label_clock = Label(self.master, bd=20)
        self.label_clock.place(relx=0.2, rely=0.02)

        ## make timetable button
        self.button_makeTimetable = Button(self.master, text='make!', cursor='hand2', width=35, height=5, font=self.button_login_font, command=self.make_timetable)
        self.button_makeTimetable.place(relx=0.015, rely=0.7)

    ###################### Login Window ######################
    def loginWindow(self):
        self.login_window = Toplevel(root)
        self.login_window.wm_attributes("-topmost", 1)
        self.login_window.bind('<Return>', self.enter_login)
        self.login_window.title('loginWindow')
        self.login_window.geometry("300x150+500+300")
        self.login_window.resizable(False, False)
        # initial settings
        self.login_set_widgets()

    def login_set_widgets(self):
        # id/pw label
        self.label_login_id = Label(self.login_window, text='Id')
        self.label_login_id.place(relx=0.1, rely=0.1)
        self.label_login_pw = Label(self.login_window, text='Password')
        self.label_login_pw.place(relx=0.1, rely=0.25)
        # id/pw input
        self.entry_id = Entry(self.login_window, width=22)
        self.entry_id.place(relx=0.32, rely=0.1)
        self.entry_pw = Entry(self.login_window, show="*", width=22)
        self.entry_pw.place(relx=0.32, rely=0.25)
        # login button
        self.button_login_login = Button(self.login_window, text='Log in',  cursor='hand2', width=15, height=2, command=self.confirm_login)
        self.button_login_login.place(relx=0.32, rely=0.5)

    def enter_login(self, event):    # user can just press the (Enter key) without clicking the login button.
        self.confirm_login()

    def confirm_login(self):
        # using input (id,pw), login to "https://icampus.skku.edu/"
        # 1. try to log in 2. get courses data 3. get student info 4. update user info
        login_id = self.entry_id.get()
        login_pw = self.entry_pw.get()
        self.driver = webdriver.Chrome(os.path.join(chromedriver_directory, 'chromedriver.exe'), options=options)  # chromewebdriver path
        self.icampus = iCampus(self.driver)
        if self.icampus.login(login_id, login_pw):
            self.icampus.get_courses()
            self.icampus.get_id()
            self.icampus.get_token()
            self.icampus.get_student_info()
            self.update_user_info()
            self.login_window.destroy()
            self.login_status = True
        else:
            self.driver.quit()
            self.login_window.destroy()
            messagebox.showerror('error',"The username or password you entered is incorrect.")

    def update_user_info(self):    # mainWindow - (user name, student id) update
        self.listBox_info.delete(0, END)
        self.listBox_info.insert(0, self.icampus.user_name)
        self.listBox_info.insert(1, self.icampus.student_id)
    ##########################################################

    ##################### Settings Window ####################
    def settingsWindow(self):
        self.settings_window = Toplevel(root)
        self.settings_window.wm_attributes("-topmost", True)
        self.settings_window.title('settingsWindow')
        self.settings_window.geometry("800x600+400+200")
        # initial settings
        self.settings_set_widgets()
        self.settings_check_login_status()    # check if login status == True

    def settings_check_login_status(self):    
        # check if the course list has been updated; 
        # if True: use (course list) data; else: pass
        # course info is stored in 'schedule_data.p'
        if self.login_status and self.settings_status:
            with open(os.path.join(program_directory, 'schedule_data.p'), 'rb') as file:
                self.courses_lecture_dict = pickle.load(file)
            self.settings_update_lectures()

    def settings_set_widgets(self):
        # Treeview - display all lectures
        self.treeView_settings_courses = ttk.Treeview(self.settings_window, selectmode='browse', height=15, columns=['1','2','3','4'], displaycolumns=['1','2','3','4'])
        self.treeView_settings_courses.column('#0', width=40)
        self.treeView_settings_courses.heading('#0', text='#')
        self.treeView_settings_courses.column('#1', width=140)
        self.treeView_settings_courses.heading('#1', text='course')
        self.treeView_settings_courses.column('#2', width=185)
        self.treeView_settings_courses.heading('#2', text='lecture')
        self.treeView_settings_courses.column('#3', width=65)
        self.treeView_settings_courses.heading('#3', text='due_at')
        self.treeView_settings_courses.column('#4', width=130)
        self.treeView_settings_courses.heading('#4', text='id')
        self.treeView_settings_courses['displaycolumns'] = ['1','2','3']
        self.treeView_settings_courses.bind('<<TreeviewSelect>>', self.settings_click_lecture)
        self.treeView_settings_courses.place(x=15, y=50)
        # List - display information about the selected lecture
        self.treeView_settings_lectureInfo = ttk.Treeview(self.settings_window, height=15, columns=['1'], displaycolumns=['1'])
        self.treeView_settings_lectureInfo.column('#0', width=100)
        self.treeView_settings_lectureInfo.heading('#0', text='info')
        self.treeView_settings_lectureInfo.column('#1', width=200)
        self.treeView_settings_lectureInfo.heading('#1', text='value')
        self.treeView_settings_lectureInfo.place(x=450, y=50)
        ### Buttons
        # update button
        self.button_settings_update = Button(self.settings_window, text='update', width=5, height=1, cursor='hand2', font=self.button_login_font, command=self.settings_get_lectures)
        self.button_settings_update.place(relx=0.02, rely=0.03)
        # add button
        self.button_settings_add = Button(self.settings_window, text='add', width=20, height=4, cursor='hand2', font=self.button_login_font, command=self.settings_add_lecture)
        self.button_settings_add.place(relx=0.02, rely=0.65)
        # delete button
        self.button_settings_delete = Button(self.settings_window, text='delete', width=20, height=4, cursor='hand2', font=self.button_login_font, command=self.settings_delete_lecture)
        self.button_settings_delete.place(relx=0.02, rely=0.8)
        # apply button
        self.button_settings_apply = Button(self.settings_window, text='Apply', width=20, height=4, cursor='hand2', font=self.button_login_font, command=self.settings_apply)
        self.button_settings_apply.place(relx=0.7, rely=0.8)

        ## set lecture time
        # label
        self.label_set_duration = Label(self.settings_window, text='set lecture duration', font=self.button_login_font)
        self.label_set_duration.place(relx=0.562, rely=0.65)
        # input
        self.spinbox_set_duration = Spinbox(self.settings_window, from_=15, to=480, increment=15)
        self.spinbox_set_duration.place(relx=0.58, rely=0.7)
        # button
        self.button_set_duration = Button(self.settings_window, text='set', width=10, height=1, cursor='hand2', font=self.button_login_font, command=self.settings_set_duration)
        self.button_set_duration.place(relx=0.75, rely=0.7)

    def settings_get_lectures(self):
        # get course-lecture data in json format
        # store course-lecture data in 'schedule_data.p'
        self.courses_lecture_dict = self.icampus.get_json()
        self.courses_dict = self.icampus.courses_dict    # (name) and (id) of all courses
        with open(os.path.join(program_directory, 'schedule_data.p'), 'wb') as file:
            pickle.dump(self.courses_lecture_dict, file)
        self.settings_update_lectures()

    def settings_update_lectures(self):
        # reset treeview before appending data
        # treeview displays ['coursename', 'lecture title', 'lecture due'] # not display 'lecture id'; is value to specify the lecture
        self.treeView_settings_courses.delete(*self.treeView_settings_courses.get_children())
        for i, info in enumerate(self.courses_lecture_dict):
            lecture = lecture_info(info)
            self.treeView_settings_courses.insert('', 'end', text=i+1, values=(lecture.course_name_ul(), lecture.title(), lecture.due_kst_ul(), lecture.id()), iid=i)
        self.settings_status = True
        self.settings_update_status = True

    def settings_click_lecture(self, event):
        # if user select lecture in treeView: shows lecture info in this list widget
        # displays ['coursename', 'lecture title', 'lecture unlock datetime', 'lecture due datetime', 'lecture type', 'lecture duration']
        try:
            selected_item = self.treeView_settings_courses.focus()
        except:
            return
        values = self.treeView_settings_courses.item(selected_item).get('values')
        lecture_id = values[3]
        self.treeView_settings_lectureInfo.delete(*self.treeView_settings_lectureInfo.get_children())
        lecture = self.settings_check_lecture_id(lecture_id)
        self.treeView_settings_lectureInfo.insert('', 'end', text='course', values=(lecture.course_name_cl(), 'None'))
        self.treeView_settings_lectureInfo.insert('', 'end', text='lecture', values=(lecture.title(), 'None'))
        self.treeView_settings_lectureInfo.insert('', 'end', text='unlock at', values=(lecture.unlock_kst_cl(), 'None'))
        self.treeView_settings_lectureInfo.insert('', 'end', text='due at', values=(lecture.due_kst_cl(), 'None'))
        self.treeView_settings_lectureInfo.insert('', 'end', text='lecture type', values=(lecture.lecture_type(), 'None'))
        self.treeView_settings_lectureInfo.insert('', 'end', text='lecture time', value=(lecture.duration_cl(), 'None'))

    def settings_add_lecture(self):    # open (add window)
        if not self.settings_update_status:
            self.settings_error_message('You must update lectures first')
            return
        self.settings_window.wm_attributes("-topmost", False)
        self.addLectureWindow()

    def settings_delete_lecture(self):    # delete selected lecture
        try:
            selected_item = self.treeView_settings_courses.focus()
        except:
            self.settings_error_message('You must select lecture first')
            return
        self.treeView_settings_courses.delete(selected_item)
        self.treeView_settings_lectureInfo.delete(*self.treeView_settings_lectureInfo.get_children())
        self.treeView_settings_lectureInfo.insert('', 'end', text='*', values=('Lecture Deleted', 'None'))
        
    def settings_set_duration(self):
        try:
            selected_item = self.treeView_settings_courses.focus()
        except:
            self.settings_error_message('You must select lecture first')
            return
        values = self.treeView_settings_courses.item(selected_item).get('values')
        lecture_id = values[3]
        lecture = self.settings_check_lecture_id(lecture_id)
        if not lecture.duration() == None:
            self.settings_error_message('You must select lecture with no duration')
            return
        input_minute = self.spinbox_set_duration.get()
        try:
            input_minute = int(input_minute)
        except:
            self.settings_error_message("You must enter numbers in the duration input field")
            return
        if input_minute < 1 or input_minute > 600:
            self.settings_error_message("You must enter valid value in the duration input field\n* number between 1 and 600")
            return
        input_duration = 60*input_minute
        for l in self.courses_lecture_dict:
            if l['component_id'] == lecture.id():
                l['commons_content'] = {'duration':input_duration}
                break
        self.settings_click_lecture(None)
        

    def settings_apply(self):
        # apply lectures in settings_treeview to mainwindow_treeview
        # if there is no 'lecture duration': not apply
        for i in self.treeView_settings_courses.get_children():
            lecture = self.treeView_settings_courses.item(i)
            values = lecture.get('values')
            lecture_id = values[3]
            lecture = self.settings_check_lecture_id(lecture_id)
            if lecture.duration_cl() == 'None':
                continue
            self.lectures_list.append(lecture)
        self.timetable_0.append_lecture_list(self.lectures_list)
        self.timetable_1.append_lecture_list(self.lectures_list)
        self.update_lectures()
        self.settings_window.destroy()
    
    def settings_check_lecture_id(self, lecture_id):
        for lec in self.courses_lecture_dict:
            lecture = lecture_info(lec)
            if lecture.id() == lecture_id:
                return lecture

    def settings_error_message(self, error_message):    # show error messages
        self.settings_window.wm_attributes("-topmost", False)
        error = messagebox.showerror('error', error_message)
        if error == 'ok':
            self.settings_window.wm_attributes("-topmost", True)

    ################### settings_add_lecture #################
    def addLectureWindow(self):
        self.addLec_window = Toplevel(root)
        self.addLec_window.wm_attributes("-topmost", 1)
        self.addLec_window.title('addWindow')
        self.addLec_window.geometry("500x400+400+200")
        # initial settings
        self.addLec_set_vars()
        self.addLec_set_widgets()

    def addLec_set_vars(self):
        self.courses_name_list = list()
        for course_name in self.courses_dict:
            self.courses_name_list.append(course_name)
    
    def addLec_set_widgets(self):
        # labels
        self.label_addLec_course = Label(self.addLec_window, text='course')
        self.label_addLec_lecture = Label(self.addLec_window, text='lecture / content')
        self.label_addLec_due = Label(self.addLec_window, text='due')
        self.label_addLec_duration = Label(self.addLec_window, text='duration (minute)')
        self.label_addLec_course.place(relx=0.05, rely=0.1)
        self.label_addLec_lecture.place(relx=0.05, rely=0.3)
        self.label_addLec_due.place(relx=0.05, rely=0.5)
        self.label_addLec_duration.place(relx=0.05, rely=0.7)
        # course input
        self.combobox_addLec_lectures = ttk.Combobox(self.addLec_window, width=25, height=20, state='readonly', values=self.courses_name_list)
        self.combobox_addLec_lectures.place(relx=0.5, rely=0.1)
        self.combobox_addLec_lectures.set("Select Course")
        # lecture name input
        self.entry_addLec_lecture = Entry(self.addLec_window, width=25)
        self.entry_addLec_lecture.place(relx=0.5, rely=0.3)
        # due input
        self.calendar_addLec_due = DateEntry(self.addLec_window, showweeknumbers=False, firstweekday='monday', mindate=datetime_info(0,0,'datetime'), maxdate=datetime_info(1,6,'datetime'))
        self.calendar_addLec_due.place(relx=0.5, rely=0.5)
        # duration input
        self.spinbox_addLec_duration = Spinbox(self.addLec_window, from_=15, to=480, increment=15)
        self.spinbox_addLec_duration.place(relx=0.5, rely=0.7)
        # add button
        self.button_addLec_add = Button(self.addLec_window, text='add', width=20, height=3, cursor='hand2', font=self.button_login_font, command=self.addLec_add_lecture)
        self.button_addLec_add.place(relx=0.6, rely=0.8)

    def addLec_add_lecture(self):
        if not self.addLec_check_input_valid():
            return
        self.input_unlock = datetime_info(0,0,'datetime') - timedelta(hours=9)
        self.input_due = datetime.fromisoformat(str(self.input_due)) + timedelta(hours=15)
        self.input_unlock = self.input_unlock.strftime('%Y-%m-%dT%H:%M:%SZ') 
        self.input_due = self.input_due.strftime('%Y-%m-%dT%H:%M:%SZ') 
        lecture = {
            'component_id': random_int(10),
            'title': self.input_title,
            'commons_content': {'duration': self.input_duration},
            'due_at': self.input_due,
            'unlock_at': self.input_unlock,
            'type': 'assignment',
            'course_name': self.input_course_name,
            'course_id': self.input_course_id,
            }
        self.courses_lecture_dict.append(lecture)
        self.settings_update_lectures()
        self.addLec_window.destroy()
        self.settings_window.wm_attributes("-topmost", True)

    def addLec_check_input_valid(self):
        self.input_course_name = self.combobox_addLec_lectures.get()
        if self.input_course_name == 'Select Course':
            self.addLec_error_message("You must select course.")
            return False
        self.input_course_id = self.courses_dict[self.input_course_name]    # str
        self.input_title = self.entry_addLec_lecture.get()
        if self.input_title == '':
            self.addLec_error_message("You must enter the content.")
            return False
        self.input_due = self.calendar_addLec_due.get_date()    # YYYY-MM-DD
        self.input_minute = self.spinbox_addLec_duration.get()    # string type 으로 받음
        try:
            self.input_minute = int(self.input_minute)
        except:
            self.addLec_error_message("You must enter numbers in the duration input field")
            return False
        if self.input_minute < 1 or self.input_minute > 600:
            self.addLec_error_message("You must enter valid value in the duration input field\n* number between 1 and 600")
            return False
        self.input_duration = 60*self.input_minute
        return True
        
    def addLec_error_message(self, error_message):
        self.addLec_window.wm_attributes("-topmost", False)
        error = messagebox.showerror('error', error_message)
        if error == 'ok':
            self.settings_window.lift()
            self.addLec_window.wm_attributes("-topmost", True)

    ##########################################################
    ######################## Functions #######################
    def change_label_title(self, event):
        if str(event.type) == '7':
            self.label_title['text'] = ('TEAM Sungkyunkwan Schedule')
        else:
            self.label_title['text'] = ('iCampus Schedule')

    def open_loginWindow(self):
        if self.login_status == False:
            self.loginWindow()
        else:
            messagebox.showerror('error',"You are already logged in")

    def open_settingsWindow(self):
        if self.login_status == True:
            self.settingsWindow()
        else:
            messagebox.showerror('error',"You must login first.")

    def update_clock(self):
        now = datetime.today()
        if now.day != self.today.day:
            check_timetable_date(now, self.timetable_0)
            self.today = datetime.today()
        now_str = now.strftime('%Y / %m / %d\n%H : %M : %S')
        self.label_clock.configure(text=now_str)
        self.master.after(1000, self.update_clock)    # updates clock time every 1000ms

    def update_lectures(self):
        self.treeView_courses.delete(*self.treeView_courses.get_children())    # reset treeview
        total_n_time = 0
        for i, lecture in enumerate(self.lectures_list):
            if type(lecture.duration_cl()) == str:
                continue
            total_n_time += lecture.duration()
            self.treeView_courses.insert('', 'end', text=i, values=(lecture.course_name_ul(), lecture.title(), lecture.duration_cl(), lecture.id()), iid=i)
        self.label_needed_cell.configure(text=f'needed cells: {cell_needed(total_n_time)}')

    def switch_timetable(self, current_week):
        if current_week == 0:
            self.frame_timetable.place_forget()
            self.frame_timetable_2.place(relx=0.2, rely=0.1)
            self.message_week['text'] = week_info(1)
            self.timetable_1.change_label_selected_cell()
        else:
            self.frame_timetable_2.place_forget()
            self.frame_timetable.place(relx=0.2, rely=0.1)
            self.message_week['text'] = week_info(0)
            self.timetable_0.change_label_selected_cell()

    def make_timetable(self):
        selected_time = [self.timetable_0.clicked_buttons,self.timetable_1.clicked_buttons]
        time_matrix = timeMatrix()
        self.lectures_dict = dict()
        for n_lecture, lecture in enumerate(self.lectures_list):
            self.lectures_dict[n_lecture] = lecture.title()
            l_t_index = lecture.final_time_list(selected_time)
            if not time_matrix.append_lecture(n_lecture, l_t_index):
                messagebox.showerror('error',f"lecture has not been added to the timetable from the {n_lecture}th lecture.\nPlease select more cells.")
                return
        self.opt_matrix = time_matrix.get_opt_matrix()
        self.matrix_to_timetable()

    def matrix_to_timetable(self):
        # 각 cell 에 강의 넣기
        week_0 = self.opt_matrix[0]
        week_1 = self.opt_matrix[1]
        for i, cell in enumerate(week_0):
            if cell == None or cell == False:
                continue
            text = ''
            for j, info in enumerate(cell[0]):
                if j == 0:
                    text = self.lectures_dict[info]
                    continue
                text += f', {self.lectures_dict[info]}'
            self.timetable_0.table_cell[i]['text'] = text
            self.timetable_0.table_cell[i]['background'] = '#BCBDC6'
        for i, cell in enumerate(week_1):
            if cell == None or cell == False:
                continue
            text = ''
            for j, info in enumerate(cell[0]):
                if j == 0:
                    text = self.lectures_dict[info]
                    continue
                text += f', {self.lectures_dict[info]}'
            self.timetable_1.table_cell[i]['text'] = text
            self.timetable_1.table_cell[i]['background'] = '#BCBDC6'


    
    ##########################################################

### initial settings ###
# set (directory, data file, webdriver
program_directory = os.path.dirname(os.path.abspath(__file__))    # current directory
chromedriver_directory = None
pickle_directory = os.path.join(program_directory, 'data')
options = webdriver.ChromeOptions()    # chromedriver option
options.add_argument("headless")       # run chromedriver as headless

# start program
if __name__ == '__main__':
    root = Tk()
    app = Application(master=root)
    app.mainloop()

    

    