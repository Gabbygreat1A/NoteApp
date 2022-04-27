import ast
import datetime
import os
import re

from PIL import Image as EditImage
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import NoTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import get_hex_from_color, get_color_from_hex
from kivymd.app import MDApp
from kivymd.color_definitions import palette, colors
from kivymd.icon_definitions import md_icons
from kivymd.theming import ThemableBehavior
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.button import MDIconButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import IRightBodyTouch, OneLineListItem, OneLineIconListItem
from kivymd.uix.picker import MDTimePicker, MDDatePicker
from kivymd.uix.screen import MDScreen
from kivymd.uix.selectioncontrol import MDCheckbox

kv = '''
ScreenManager:
	id: manager
	Default
		main: app
		id: default
	Note:
		id: note
		main: app
		on_pre_enter:
			app.set_datetime = None
	NoteEdit:
		main: app
		id: noteedit
		name: 'noteedit'

'''


class SaveButton(MDIconButton):
    pass


class NewSaveButton(SaveButton):
    pass


class EditSaveButton(SaveButton):
    pass


class CustomTimePicker(MDTimePicker):
    def _switch_input(self):
        pass


class ToggleBox(IRightBodyTouch, MDCheckbox):
    pass


class CustomDatePicker(MDDatePicker):
    def transformation_to_dialog_input_date(self):
        pass


class ColorListItem(OneLineIconListItem):
    text = StringProperty()
    icon = StringProperty()
    text_color = ListProperty([0, 0, 0, 0])


class AppBaseDialog(ThemableBehavior, ModalView):
    pass


class AppDialogChangeColor(AppBaseDialog):
    def set_list_colors_themes(self):
        for name_theme in palette:
            self.ids.rv.data.append(
                {
                    'viewclass': 'ColorListItem',
                    'icon': 'format-color-fill',
                    'text_color': get_color_from_hex(colors[name_theme]['500']),
                    'text': name_theme,
                }
            )


class NameFieldBox(MDBoxLayout):
    pass


class SettingOneLine(OneLineListItem):
    pass


class AboutApp(AppBaseDialog):
    shown = None

    def on_open(self):
        Animation(font_size=30, duration=2).start(self.ids.header)
        Animation(opacity=1, duration=2).start(self.ids.about_text)
        if not self.shown:
            with open('Texts/AboutApp.txt', 'r') as file:
                self.shown = file.read()
            self.ids.about_text.text = self.shown

    def on_dismiss(self):
        self.ids.header.font_size = 1
        self.ids.about_text.opacity = 0


class AppUsage(AppBaseDialog):
    shown = None

    def on_open(self):
        Animation(font_size=30, duration=2).start(self.ids.header)
        Animation(opacity=1, duration=2).start(self.ids.app_usage)
        if not self.shown:
            with open('Texts/AppUsage.txt', 'r')as file:
                self.shown = file.read()
            self.ids.app_usage.text = self.shown

    def on_dismiss(self):
        self.ids.header.font_size = 1
        self.ids.app_usage.opacity = 0


class EmailFieldBox(MDBoxLayout):
    pass


class ImageSetter(MDFloatLayout):
    main = ObjectProperty()
    source = StringProperty()

    def snap(self):
        if self.main.config.get('General', 'user_image') != 'Images/defaultImage.png':
            os.unlink(self.main.config.get('General', 'user_image'))
        self.newImage = os.path.join('Images', 'userImage.png')
        self.image = EditImage.open(self.source)
        self.image.thumbnail((300, 300))
        self.image.save(self.newImage)
        self.main.config.set('General', 'user_image', self.newImage)
        self.main.config.update_config('main.ini')
        toast(f'{os.path.split(self.source)[1]} Restart App To See Update...', duration=3,
              background=self.main.theme_cls.primary_dark)
        self.main.root.ids.default.ids.setting.ids.manager.current = 'setting'


class CustomFileManager(MDFileManager):
    main = ObjectProperty()

    def select_directory_on_press_button(self, *args):
        toast('Please Select An Image File!', background=self.main.theme_cls.primary_dark)


class Setting(MDScreen):
    main = ObjectProperty()
    manager_open = False
    path = StringProperty()
    app_change_color = None
    restoreField = None
    emailField = None
    nameField = None

    def __init__(self, **kwargs):
        super(Setting, self).__init__(**kwargs)
        self.file_manager = CustomFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=False,
            ext=['.png', '.jpg', '.jpeg']
        )

    def file_manager_open(self):
        self.file_manager.show('/')  # output manager to the screen
        self.manager_open = True

    def select_path(self, path):
        self.exit_manager()
        self.path = path.replace('\\', '/')
        self.main.root.ids.default.ids.setting.ids.manager.current = 'editimage'

    def exit_manager(self, *args):
        self.manager_open = False
        self.file_manager.close()

    def restoreDefault(self):
        def restore():
            self.main.resetSettings()
            self.main.theme_cls.theme_style = self.main.config.get('General', 'theme_color')
            self.main.contentbody.ids.achieved.text = 'Achieved Tasks: ' + self.main.config.get('General',
                                                                                                'achieve_counter')
            self.main.theme_cls.primary_palette = self.main.config.get('General', 'palette')
            self.main.contentbody.ids.user_name.text = self.main.config.get('General', 'user_name')
            self.main.root.ids.default.ids.setting.ids.name.secondary_text = self.main.config.get('General',
                                                                                                  'user_name')
            self.main.root.ids.default.ids.setting.ids.email.secondary_text = self.main.config.get('General',
                                                                                                   'user_email')
            self.restoreField.dismiss()
            toast('All Settings And User Data Has Been Reset...', background=self.main.theme_cls.primary_dark)

        if not self.restoreField:
            self.restoreField = MDDialog(title='Do You Want To Reset All Settings And User Data?',
                                         auto_dismiss=True,
                                         text='[b]All Data And User Setting Will Be Reset[/b]',
                                         buttons=[
                                             MDFlatButton(text='CANCEL',
                                                          on_press=lambda x: self.restoreField.dismiss()),
                                             MDRaisedButton(text='PROCEED', on_press=lambda x: restore())])
        self.restoreField.open()

    def openNameField(self):
        if not self.nameField:
            self.name_field_box = NameFieldBox()
            self.nameField = MDDialog(auto_dismiss=True,
                                      content_cls=self.name_field_box,
                                      type='custom',
                                      pos_hint={'center_y': .6},
                                      buttons=[
                                          MDFlatButton(text='CANCEL', on_press=lambda x: self.nameField.dismiss()),
                                          MDRaisedButton(text='SAVE', on_release=lambda x: self.setName(
                                              self.name_field_box.ids.name.text))]
                                      )
        self.name_field_box.ids.name.focused = True
        self.nameField.open()

    def openEmailField(self):
        if not self.emailField:
            self.email_field_box = EmailFieldBox()
            self.emailField = MDDialog(auto_dismiss=True,
                                       content_cls=self.email_field_box,
                                       type='custom',
                                       pos_hint={'center_y': .6},
                                       buttons=[
                                           MDFlatButton(text='CANCEL', on_press=lambda x: self.emailField.dismiss()),
                                           MDRaisedButton(text='SAVE', on_release=lambda x: self.setEmail(
                                               self.email_field_box.ids.name.text))]
                                       )
        self.email_field_box.ids.name.focused = True
        self.emailField.open()

    def setName(self, name):
        self.nameField.dismiss()
        if 0 < len(name.strip()) <= 15:
            self.main.contentbody.ids.user_name.text = name
            self.main.root.ids.default.ids.setting.ids.name.secondary_text = name
            self.main.config.set('General', 'user_name', name)
            self.main.config.update_config('main.ini')
            toast(f'{name.strip()} Set As User Name', background=self.main.theme_cls.primary_dark)

    def setEmail(self, mail):
        self.emailField.dismiss()
        if 0 < len(mail.strip()) <= 40:
            self.main.root.ids.default.ids.setting.ids.email.secondary_text = mail
            self.main.config.set('General', 'user_email', mail)
            self.main.config.update_config('main.ini')
            toast(f'{mail.strip()} Set As Email Address', background=self.main.theme_cls.primary_dark)
        # set regex for Email

    def setAppColor(self):
        if not self.app_change_color:
            self.app_change_color = AppDialogChangeColor()
            self.app_change_color.set_list_colors_themes()
        self.app_change_color.open()


class HistoryList(MDBoxLayout):
    pass


class HistoryInfo(AppBaseDialog):
    text = StringProperty()
    info = StringProperty()


class HistoryNote(MDBoxLayout):
    text = StringProperty()
    main = ObjectProperty()


class History(MDScreen):
    main = ObjectProperty()

    def __init__(self, **kwargs):
        super(History, self).__init__(**kwargs)
        self.history_note = HistoryNote()

    def on_pre_enter(self):
        self.sameDay = 0
        self.sameDayHold = []
        self.noDeadline = 0
        self.noDeadlineHold = []
        self.tomorrow = 0
        self.tomorrowHold = []
        self.others = 0
        self.othersHold = []
        self.date = datetime.datetime.today()
        self.ids.active_label.ids.text.text = f'Active Task(s): {len(list(self.main.config["Notes"]))}'
        for note in self.main.config['Notes']:
            now = self.main.formatDay(self.date)
            deadline = ast.literal_eval(self.main.config.get('Notes', note))[2]
            if '@' in deadline and (now[:now.index('@')] == deadline[:deadline.index('@')]):
                self.sameDay += 1
                self.sameDayHold.append(note)
            elif '@' in deadline and (now[:now.index('@')] != deadline[:deadline.index('@')]):
                now_date = re.search(r'\d{1,2}', now[:now.index('@')]).group(0)
                dead_date = re.search(r'\d{1,2}', deadline[:deadline.index('@')]).group(0)
                if int(dead_date) - int(now_date) == 1:
                    self.tomorrow += 1
                    self.tomorrowHold.append(note)
                else:
                    self.others += 1
                    self.othersHold.append(note)
            elif '@' not in deadline:
                self.noDeadline += 1
                self.noDeadlineHold.append(note)
        self.ids.today_label.ids.text.text = f'Today\'s Task(s): {self.sameDay}'
        self.ids.today_label.ids.icon.icon = 'calendar-today'
        self.ids.active_label.ids.icon.icon = 'tooltip-check-outline'
        self.ids.tomorrow_label.ids.text.text = f'Tommorow\'s Task(s): {self.tomorrow}'
        self.ids.tomorrow_label.ids.icon.icon = 'calendar-end'
        self.ids.no_deadline.ids.text.text = f'No Set Deadline: {self.noDeadline}'
        self.ids.no_deadline.ids.icon.icon = 'calendar-remove'
        self.ids.others_label.ids.text.text = f'Later Task(s): {self.others}'
        self.ids.others_label.ids.icon.icon = 'calendar-start'
        self.ids.achieved_label.ids.text.text = f"Achieved Task(s): {self.main.config.get('General', 'achieve_counter')}"
        self.ids.achieved_label.ids.text.text_color = get_color_from_hex('#40ff00')
        self.ids.achieved_label.ids.button.disabled = True
        self.ids.achieved_label.ids.button.text = 'Number Of Achieved Schedules'
        self.ids.achieved_label.ids.icon.icon = 'gift-outline'
        self.ids.ignored_label.ids.text.text = f"Ignored Task(s): {self.main.config.get('General', 'ignore_counter')}"
        self.ids.ignored_label.ids.text.text_color = get_color_from_hex('#ff0000')
        self.ids.ignored_label.ids.button.disabled = True
        self.ids.ignored_label.ids.button.text = 'Number Of Ignored Schedules'
        self.ids.ignored_label.ids.icon.icon = 'call-missed'

    def resetHistory(self):
        def reset():
            self.ids.achieved_label.ids.text.text = f'[color=#40ff00]Achieved Task(s): 0[/color]'
            self.ids.ignored_label.ids.text.text = f'[color=#ff0000]Ignored Task(s): 0[/color]'
            self.main.config.set('General', 'ignore_counter', 0)
            self.main.config.set('General', 'achieve_counter', 0)
            self.main.config.update_config('main.ini')
            self.resetField.dismiss()
            toast('Cleared Saved History Successfully...', background=self.main.theme_cls.primary_dark)

        self.resetField = MDDialog(title='Do You Want To Clear \'Achieved\' And \'Ignored\' Data?',
                                   auto_dismiss=True,
                                   text='[b]All Saved Data For Achieved And Ignored Schedules Will Be Cleared...[/b]',
                                   buttons=[
                                       MDFlatButton(text='CANCEL', on_press=lambda x: self.resetField.dismiss()),
                                       MDRaisedButton(text='PROCEED', on_press=lambda x: reset())])
        self.resetField.open()

    def open_history_info(self, ins):
        number = int(re.search(r'\d{1}', ins).group(0))

        def which(box):
            for i in box:
                self.history_info.ids.box.add_widget(HistoryNote(text=i))

        if number == 0:
            toast('Nothing To View Here...', background=self.main.theme_cls.primary_dark)
        else:
            self.history_info = HistoryInfo(text=ins)
            if ins.startswith('Active'):
                which(self.main.config['Notes'])
            elif ins.startswith('Today'):
                which(self.sameDayHold)
            elif ins.startswith('Tommorow'):
                which(self.tomorrowHold)
            elif ins.startswith('No'):
                which(self.noDeadlineHold)
            elif ins.startswith('Later'):
                which(self.othersHold)
            self.history_info.open()


class Default(MDScreen):
    main = ObjectProperty()


class Note(MDScreen):
    main = ObjectProperty()

    def toogleSaveButton(self, title, desc):
        self.addButton()

        def validityChecks():
            if len(title.text.strip()) == 0:
                return False
            elif self.main.config.has_option('Notes', title.text.strip()):
                return False
            elif len(desc.text.strip()) == 0 or len(desc.text.strip()) > 500:
                return False
            else:
                return True

        if validityChecks():
            self.main.newsavebutton.disabled = False
            Animation(opacity=1).start(self.main.newsavebutton)

            self.main.editsavebutton.disabled = False
            Animation(opacity=1).start(self.main.editsavebutton)
        else:
            Animation(opacity=0).start(self.main.newsavebutton)
            self.main.newsavebutton.disabled = True

            Animation(opacity=0).start(self.main.editsavebutton)
            self.main.editsavebutton.disabled = True

    def addButton(self):
        for child in self.ids.savebox.children:
            self.ids.savebox.remove_widget(child)
        self.main.update_config('main.ini')
        self.ids.savebox.add_widget(self.main.newsavebutton)


class NoteEdit(Note):
    edit_text = StringProperty()

    def addButton(self):
        for child in self.ids.savebox.children:
            self.ids.savebox.remove_widget(child)
        self.main.update_config('main.ini')
        self.ids.savebox.add_widget(self.main.editsavebutton)


class EmptyNote(MDBoxLayout):
    pass


class RevealBox(MDBoxLayout):
    text = StringProperty()


class NoteLeave(MDCard):
    title = StringProperty()
    date = StringProperty()
    deadline = StringProperty()
    desc = StringProperty()
    revealed = False
    main = ObjectProperty()

    def reveal(self, desc, icon):
        if self.revealed:
            icon.icon = 'eye'
            self.height = '150dp'
            self.ids.descbox.remove_widget(self.revealbox)
        else:
            icon.icon = 'eye-off'
            self.revealbox = RevealBox(text=desc)
            self.height = '250dp'
            self.ids.descbox.add_widget(self.revealbox)
        self.revealed = not self.revealed

    def editNote(self, title, desc, deadline):
        self.main.set_datetime = 'None'
        self.main.root.ids.noteedit.edit_title = title
        self.main.root.ids.noteedit.ids.title.text = title
        self.main.root.ids.noteedit.ids.desc.text = desc
        self.main.root.ids.noteedit.ids.desc.focused = True
        self.main.root.ids.noteedit.ids.title.focused = True
        if deadline == 'None':
            self.main.root.ids.noteedit.ids.deadline.text = 'Not Set'
        else:
            self.main.root.ids.noteedit.ids.deadline.text = deadline
        self.main.changeScreen('noteedit')


class ContentBody(MDBoxLayout):
    pass


class ScrollBody(ScrollView):
    pass


class Main(MDApp):
    def build_config(self, config):
        config.setdefaults('General', {'theme_color': 'Light',
                                       'achieve_counter': 0,
                                       'ignore_counter': 0,
                                       'user_image': 'Images/defaultImage.png',
                                       'user_name': 'Default User',
                                       'user_email': 'You Have Not Set Any Email',
                                       'palette': 'Cyan'}
                           )
        config.add_section('Notes')

    def resetSettings(self):
        self.config.set('General', 'theme_color', 'Light')
        self.config.set('General', 'achieve_counter', 0)
        self.config.set('General', 'ignore_counter', 0)
        self.config.set('General', 'user_image', 'Images/defaultImage.png')
        self.config.set('General', 'user_name', 'Default User')
        self.config.set('General', 'user_email', 'You Have Not Set Any Email')
        self.config.set('General', 'palette', 'Cyan')
        self.config.update_config('main.ini')

    def build(self):
        Window.bind(on_keyboard=self.events)
        for screen in os.listdir('Screens'):
            Builder.load_file(os.path.join('Screens', screen))

        self.theme_cls.theme_style = self.config.get('General', 'theme_color')
        self.theme_cls.primary_palette = self.config.get('General', 'palette')

        return Builder.load_string(kv)

    def on_start(self):
        self.newsavebutton = NewSaveButton()
        self.editsavebutton = EditSaveButton()
        self.contentbody = ContentBody()
        self.aboutapp = AboutApp()
        self.app_usage = AppUsage()
        self.reloadNote()
        Clock.schedule_interval(self.updateTime, 1)

    def updateTime(self, interval):
        today = datetime.datetime.today()
        format_day = self.formatDay(today)
        self.current_date = format_day[0: format_day.index('@')]
        self.contentbody.ids.date.text = f'[size=18]{self.current_date}[/size]'
        self.contentbody.ids.time.text = today.strftime('[size=40]%I:%M[/size][size=30]:%S[/size] [size=20]%p[/size]')

        try:
            for note in self.scrollbody.ids.box.children:
                if note.deadline != 'None':

                    deadline = note.deadline[0:note.deadline.index('@')]

                    date = re.search(r'\d{1,2}', deadline).group(0)
                    year = re.search(r'\d{4}', deadline).group(0)
                    month = re.findall(r'\w+', deadline)[2]

                    card_date = datetime.date(int(year), self.formatMonth(month), int(date))
                    now_date = datetime.date(today.year, today.month, today.day)
                    pos = note.deadline.index('@')
                    if ((card_date - now_date).days) <= -1:
                        try:
                            self.deleteNote(note.title, True)
                        except KeyError:
                            pass
                    elif ((card_date - now_date).days) == 0:
                        # note.md_bg_color = 10 / 255, 194 / 255, 56 / 255, 1
                        note.ids.deadline.text = f'Today{note.deadline[pos:]}'
                        note.ids.mark.opacity = 1
                        note.ids.mark.disabled = False
                    elif ((card_date - now_date).days) == 1:
                        # note.md_bg_color = 0 / 255, 125 / 255, 255 / 255, 1
                        note.ids.deadline.text = f'Tommorow{note.deadline[pos:]}'
                    elif ((card_date - now_date).days) > 1:
                        pass
                        # note.md_bg_color = self.theme_cls.primary_color
        except AttributeError:
            pass

    def events(self, window, key, *args):
        if key == 27:
            if self.root.ids.default.ids.setting.manager_open:
                self.root.ids.default.ids.setting.file_manager.back()
            elif self.root.ids.default.ids.setting.ids.manager.current != 'setting':
                self.root.ids.default.ids.setting.changeScreen('setting')
            elif self.root.current == 'default':
                self.exit()
            else:
                self.goBack()
        return True

    def proMessage(self):
        pro_field = MDDialog(title='[b]UPGRADE TO PRO![/b]',
                             auto_dismiss=True,
                             text='[b]To Fully Enjoy All Packages[/b]',
                             buttons=[
                                 MDFlatButton(text='CANCEL', on_press=lambda x: pro_field.dismiss()),
                                 MDRaisedButton(text='UPGRADE')])
        pro_field.open()

    def exit(self):
        leave = MDDialog(title='Do You Want To Leave?',
                         auto_dismiss=True,
                         buttons=[
                             MDFlatButton(text='CANCEL', on_press=lambda x: leave.dismiss()),
                             MDRaisedButton(text='QUIT', on_press=lambda x: self.stop())])
        leave.open()

    def changeScreen(self, screen):
        self.root.transition.direction = 'left'
        self.root.current = screen

    def goBack(self):
        self.root.transition.direction = 'right'
        self.root.current = 'default'
        self.root.ids.note.ids.desc.text = ''
        self.root.ids.note.ids.title.text = ''
        self.root.ids.note.ids.deadline.text = ''

    def deleteNote(self, title, show=False):
        self.config.remove_option('Notes', title)
        if not show:
            toast(f'Deleted \'{title}\' Successfully...', background=self.theme_cls.primary_dark)
        self.config.update_config('main.ini')
        self.reloadNote()

    def reloadNote(self):
        self.root.ids.default.ids.container.clear_widgets()
        if len(list(self.config['Notes'])) == 0:
            self.root.ids.default.ids.container.add_widget(EmptyNote())
        else:
            for i in range(len(self.contentbody.ids.holder.children)):
                for child in self.contentbody.ids.holder.children:
                    self.contentbody.ids.holder.remove_widget(child)
            self.scrollbody = ScrollBody()
            for note in list(self.config['Notes']):
                values = ast.literal_eval(self.config.get('Notes', note))
                title = note
                desc = values[0]
                date = values[1]
                deadline = values[2]
                self.scrollbody.ids.box.add_widget(NoteLeave(title=title, desc=desc, date=date, deadline=deadline))
            self.contentbody.ids.holder.add_widget(self.scrollbody)
            self.root.ids.default.ids.container.add_widget(self.contentbody)
            self.contentbody.ids.active_note.text = f"Active Notes: {len(list(self.config['Notes']))}"
        self.config.update_config('main.ini')

    def saveNote(self, title, desc, edit_title=False):
        # desc, date, deadline
        date = self.formatDay(datetime.datetime.today())
        if self.set_datetime:
            deadline = self.set_datetime
        else:
            deadline = 'None'
        if edit_title:
            self.deleteNote(edit_title, True)
        self.config.set('Notes', title.text, [desc.text, date, deadline])
        self.config.update_config('main.ini')
        self.changeScreen('default')
        title.text = ''
        desc.text = ''
        self.root.ids.note.ids.deadline.text = ''

    def formatMonth(self, month):
        months = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 'July': 7, 'August': 8,
                  'September': 9, 'October': 10, 'November': 11, 'December': 12}
        return months[month]

    def formatDay(self, datetime):
        day = str(datetime.day)
        if day.startswith('1'):
            suffix = 'th'
        else:
            if day.endswith('1'):
                suffix = 'st'
            elif day.endswith('2'):
                suffix = 'nd'
            elif day.endswith('3'):
                suffix = 'rd'
            else:
                suffix = 'th'
        if '{:%d}'.format(datetime).startswith('0'):
            main = '{:%d}'.format(datetime).strip('0') + suffix
        else:
            main = '{:%d}'.format(datetime) + suffix
        return '{:%A {} %B %Y@%I:%M %p}'.format(datetime, main)

    def show_time_picker(self):
        time_dialog = CustomTimePicker()
        time_dialog.bind(on_save=self.on_save_time, on_cancel=self.reset_label)
        time_dialog.open()

    def on_save_time(self, instance, value):
        self.time_value = value
        self.show_date_picker()

    def show_date_picker(self):
        date_dialog = CustomDatePicker()
        date_dialog.bind(on_save=self.get_datetime, on_cancel=self.reset_label)
        date_dialog.open()

    def get_datetime(self, instance, value, date_range):
        self.set_datetime = self.formatDay(
            datetime.datetime(value.year, value.month, value.day, self.time_value.hour, self.time_value.minute,
                              self.time_value.second))
        if self.root.current == 'note':
            self.root.ids.note.ids.deadline.text = self.set_datetime
        else:
            self.root.ids.noteedit.ids.deadline.text = self.set_datetime

    def reset_label(self, instance, value):
        self.set_datetime = None
        self.root.ids.note.ids.deadline.text = ''


Main().run()
