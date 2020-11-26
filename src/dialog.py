import os

from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import StringProperty
from functools import partial
from src.calender import CustomDatePicker
from src.db.manager import DatabaseManager
from src.common_widget import CustomCheckBox
from utils.data_tool import modify_date_form
from utils import globals
from settings import KVS_DIR

Builder.load_file(os.path.join(KVS_DIR, 'dialog_screen.kv'))


class OpenDialog(Popup):
    error = StringProperty()

    def __init__(self, time_stamp_ret, client, **kwargs):
        self.register_event_type('on_confirm')
        super(OpenDialog, self).__init__(**kwargs)
        self.date_picker = CustomDatePicker()
        self.db_manager = DatabaseManager()
        self.selected_btn = None
        self.time_stamp_data_info = []
        self.time_stamp_ret = time_stamp_ret
        self.selected_client = client

    def on_error(self, inst, text):
        if text:
            self.lb_error.size_hint_y = 1
            self.size = (400, 250)
        else:
            self.lb_error.size_hint_y = None
            self.lb_error.height = 0
            self.size = (400, 250)

    def _enter(self):
        if not self.first_text or not self.second_text:
            self.error = "Error: enter 2 dates"
        else:
            self.dispatch('on_confirm', self.first_text, self.second_text)

    def _cancel(self):
        self.dismiss()

    def on_confirm(self, *args):
        pass

    def show_calendar(self, select_btn):
        self.selected_btn = select_btn
        self.date_picker.show_popup(1, 1)
        self.date_picker.bind(on_confirm=self.select_date)

    def select_date(self, *args):
        args[0].focus = False
        selected_date = args[1]
        if self.time_stamp_ret:
            self.time_stamp_data_info = \
                self.db_manager.read_only_time_stamp(date=modify_date_form(f_date=selected_date),
                                                     client=self.selected_client)
            if len(self.time_stamp_data_info) != 0:
                time_stamp_select = TimeStampDialog(t_s_info=self.time_stamp_data_info, title="Select time stamp")
                time_stamp_select.bind(on_confirm=partial(self.get_time_stamp))
                time_stamp_select.open()
        else:
            if self.selected_btn == "1":
                self.ids.first_selected_date.text = selected_date
            else:
                self.ids.second_selected_date.text = selected_date

    def get_time_stamp(self, *args):

        args[0].dismiss()
        if self.selected_btn == "1":
            self.ids.first_selected_date.text = self.time_stamp_data_info[int(args[1])]
        else:
            self.ids.second_selected_date.text = self.time_stamp_data_info[int(args[1])]
        globals.checked_item = ""


class OpenFileDialog(Popup):
    error = StringProperty()

    def __init__(self, **kwargs):
        self.register_event_type('on_confirm')
        super(OpenFileDialog, self).__init__(**kwargs)
        self.selected_btn = None

    def on_error(self, inst, text):
        if text:
            self.lb_error.height = 30
            self.height += 30
        else:
            self.lb_error.size_hint_y = None
            self.lb_error.height = 0
            self.size -= 30

    def _enter(self):
        if not self.first_text or not self.second_text:
            self.error = "Error: enter 2 files"
        else:
            self.dispatch('on_confirm', self.first_text, self.second_text)

    def _cancel(self):
        self.dismiss()

    def on_confirm(self, *args):
        pass

    def show_file_browser(self, select_btn):
        self.selected_btn = select_btn
        file_browser = LoadDialog()
        file_browser.bind(on_confirm=partial(self.get_selected_file))
        file_browser.open()

    def get_selected_file(self, *args):
        args[0].dismiss()
        file_path = args[1]
        file_name = args[2][0]
        file_full_path = os.path.join(file_path, file_name)
        if self.selected_btn == "1":
            self.ids.first_selected_file.text = file_full_path
        else:
            self.ids.second_selected_file.text = file_full_path


class TimeStampDialog(Popup):
    error = StringProperty()

    def __init__(self, t_s_info, title, **kwargs):
        super(TimeStampDialog, self).__init__(**kwargs)
        self.register_event_type('on_confirm')
        self.title = title
        self.set_widget(t_s_info=t_s_info)

    def set_widget(self, t_s_info):
        self.ids.time_stamp.clear_widgets(self.ids.time_stamp.children[:])
        self.ids.time_stamp.cols = 2
        for i, t_s_i in enumerate(t_s_info):
            self.ids.time_stamp.add_widget(CustomCheckBox(group='check', text=str(i), size_hint_x=0.2,
                                                          color=[1.0, 1.0, 1.0, 1.0], size_hint_y=None, height=30))
            label_box = Label(size_hint_x=0.8, text=t_s_i, size_hint_y=None, height=30)
            self.ids.time_stamp.add_widget(label_box)
        self.ids.time_stamp.height = 30 * len(t_s_info)
        self.height = self.ids.time_stamp.height + 100

    def on_error(self, inst, text):
        if text:
            self.lb_error.height = 30
            self.height += 30
        else:
            self.lb_error.size_hint_y = None
            self.lb_error.height = 0
            self.size -= 30

    def _enter(self):

        if globals.checked_item == "":
            self.error = "Error: select one of above checks"
        else:
            self.dispatch('on_confirm', globals.checked_item)

    def on_confirm(self, *args):
        pass

    def _cancel(self):
        self.dismiss()


class LoadDialog(Popup):
    error = StringProperty()

    def __init__(self, **kwargs):
        super(LoadDialog, self).__init__(**kwargs)
        self.register_event_type('on_confirm')

    def on_error(self, inst, text):
        if text:
            self.lb_error.height = 30
            self.height += 30
        else:
            self.lb_error.size_hint_y = None
            self.lb_error.height = 0
            self.size -= 30

    def dismiss_popup(self):
        self.dismiss()

    def load(self):

        if not self.path or not self.filename:
            self.error = "Error: select file"
        else:
            file_ext = self.filename[0][self.filename[0].rfind(".") + 1:]
            if "ack" not in file_ext.lower():
                self.error = "Select the correct ACK file"
            else:
                self.dispatch('on_confirm', self.path, self.filename)

    def on_confirm(self, *args):
        pass


if __name__ == '__main__':

    OpenDialog(time_stamp_ret=True, client="")
