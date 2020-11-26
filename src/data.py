import os

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.properties import StringProperty
from functools import partial
from src.calender import CustomDatePicker
from src.dialog import OpenDialog, TimeStampDialog, LoadDialog, OpenFileDialog
from src.common_widget import CustomCheckBox
from src.db.manager import DatabaseManager
from utils.data_tool import extract_individual_info, modify_date_form, convert_string_float, extract_hopper_dispenser, \
    extract_file_info_file_mode
from utils import globals
from settings import KVS_DIR

Builder.load_file(os.path.join(KVS_DIR, 'data_screen.kv'))


class DataScreen(Screen):

    def __init__(self, **kwargs):
        super(DataScreen, self).__init__(**kwargs)
        self.db_manager = DatabaseManager()
        self.date_input = CustomDatePicker()
        self.info_date = None
        self.date = None
        self.first_com_date = None
        self.second_com_date = None
        self.registered_client_devices = self.db_manager.read_client_devices()
        self.selected_client = None
        self.kind = None

    def select_method(self, kind):
        self.kind = kind
        working_method = TimeStampDialog(t_s_info=["Select from files", "Select from DB"], title="Select method")
        working_method.bind(on_confirm=partial(self.get_method))
        working_method.open()

    def get_method(self, *args):
        args[0].dismiss()
        selection_method = args[1]
        globals.checked_item = ""
        if selection_method == "0":
            if self.kind == "data":
                file_browser = LoadDialog()
                file_browser.bind(on_confirm=partial(self.get_selected_file))
                file_browser.open()
            else:
                two_dates_input = OpenFileDialog()
                two_dates_input.bind(on_confirm=partial(self.get_info_two_files))
                two_dates_input.open()
        else:
            self.select_registered_client()

    def select_registered_client(self):
        if self.registered_client_devices:
            client_device_select = TimeStampDialog(t_s_info=self.registered_client_devices,
                                                   title="Select one of registered clients")
            if self.kind == "data":
                client_device_select.bind(on_confirm=partial(self.get_selected_client))
            else:
                client_device_select.bind(on_confirm=partial(self.get_selected_client_for_compare))
            client_device_select.open()
        else:
            content = Button(text='There is not any registered client.')
            popup = Popup(title='No registered Client', content=content, size_hint=(None, None),
                          size=(500, 100), auto_dismiss=False)
            content.bind(on_press=popup.dismiss)
            popup.open()

    def get_selected_client(self, *args):
        args[0].dismiss()
        self.selected_client = self.registered_client_devices[int(args[1])]
        globals.checked_item = ""
        self.date_input.show_popup(1, 0.3)
        self.date_input.bind(on_confirm=self.get_date)

    def get_date(self, *args):
        init_date = args[1]
        self.date = modify_date_form(f_date=init_date)
        print(self.date)

        self.info_date = self.db_manager.read_whole_info_date(date=self.date, client=self.selected_client)
        self.create_file_date_widget()

        return

    def create_file_date_widget(self):
        self.ids.info_screen.clear_widgets(self.ids.info_screen.children[:])
        self.ids.info_screen.add_widget(DataInfo(date_text=self.date, date_info=self.info_date,
                                                 client_info=self.selected_client))

    def get_selected_client_for_compare(self, *args):
        args[0].dismiss()
        self.selected_client = self.registered_client_devices[int(args[1])]
        globals.checked_item = ""
        two_dates_input = OpenDialog(time_stamp_ret=True, client=self.selected_client)
        two_dates_input.bind(on_confirm=partial(self.get_info_two_dates))
        two_dates_input.open()

    def get_info_two_dates(self, *args):
        args[0].dismiss()
        self.first_com_date = args[1]
        self.second_com_date = args[2]
        first_date_info = self.db_manager.read_time_stamp_file(time_stamp_date=self.first_com_date)
        second_date_info = self.db_manager.read_time_stamp_file(time_stamp_date=self.second_com_date)
        self.create_compared_date_widget(f_date_info=first_date_info, s_date_info=second_date_info)

    def create_compared_date_widget(self, f_date_info, s_date_info):
        self.ids.info_screen.clear_widgets(self.ids.info_screen.children[:])
        self.ids.info_screen.add_widget(DataCompareInfo(f_date=self.first_com_date, s_date=self.second_com_date,
                                                        f_info=f_date_info, s_info=s_date_info))

    def readout_client_response(self):
        self.ids.info_screen.clear_widgets(self.ids.info_screen.children[:])
        self.ids.info_screen.add_widget(ReadoutInfo())

    def get_selected_file(self, *args):
        args[0].dismiss()
        file_path = args[1]
        file_name = args[2][0]
        file_full_path = os.path.join(file_path, file_name)
        selected_data = extract_file_info_file_mode(full_path=file_full_path)
        machine_no = selected_data[0][selected_data[0].find(":") + 1:]
        approve_no = selected_data[1][selected_data[1].find(":") + 1:]
        pay_in_amount, pay_out_amount, balance1, balance2, file_content, operation, profit, player_burden = \
            extract_individual_info(content=selected_data)
        hopper_pipe = extract_hopper_dispenser(file_content=file_content,
                                               main_search_item=["HOPPER", "ROEHRENINHALT"])
        dispenser = extract_hopper_dispenser(file_content=file_content, main_search_item=["DISPENSERINHALT"])
        self.ids.info_screen.clear_widgets(self.ids.info_screen.children[:])
        self.ids.info_screen.add_widget(FileInfo(text_field=file_content, machine_no=machine_no, approve_no=approve_no,
                                        pay_in=pay_in_amount, pay_out=pay_out_amount, balance_1=balance1,
                                        balance_2=balance2, operation=operation, profit=profit,
                                        player_burden=player_burden, hopper=hopper_pipe, dispensers=dispenser,
                                        due_date=selected_data[2], place=selected_data[7], machine=selected_data[8]))

    def get_info_two_files(self, *args):
        args[0].dismiss()
        first_file = args[1]
        second_file = args[2]
        f_file_info = extract_file_info_file_mode(full_path=first_file)
        s_file_info = extract_file_info_file_mode(full_path=second_file)
        self.ids.info_screen.clear_widgets(self.ids.info_screen.children[:])
        self.ids.info_screen.add_widget(DataCompareInfo(f_date=f_file_info[2], s_date=s_file_info[2],
                                                        f_info=f_file_info, s_info=s_file_info))


class FileInfo(BoxLayout):
    def __init__(self, text_field, machine_no, approve_no, pay_in, pay_out, balance_1, balance_2, operation, profit,
                 player_burden, hopper, dispensers, due_date, place, machine, **kwargs):
        super(FileInfo, self).__init__(**kwargs)

        self.set_label_value(text_field, machine_no, approve_no, pay_in, pay_out, balance_1, balance_2, operation,
                             profit, player_burden, hopper, dispensers, due_date, place, machine)

    def set_label_value(self, text_field, machine_no, approve_no, pay_in, pay_out, balance_1, balance_2, operation,
                        profit, player_burden, hopper, dispensers, due_date, place, machine):
        self.ids.pop_up_date.text = due_date
        self.ids.client_place_model.text = place + " | " + machine
        self.ids.file_content.text = text_field
        self.ids.pop_up_machine_no.text = machine_no
        self.ids.pop_up_approve_no.text = approve_no
        self.ids.pop_up_pay_in.text = pay_in
        self.ids.pop_up_pay_out.text = pay_out
        self.ids.pop_up_balance1.text = balance_1
        self.ids.pop_up_balance2.text = balance_2
        self.ids.pop_up_operation.text = operation
        self.ids.pop_up_profit.text = profit
        self.ids.pop_up_player_burden.text = player_burden
        for value in hopper:
            new_box = BoxLayout(size_hint_y=None, height=31, padding=[0, 0, 0, 1])
            new_label = InfoLabel(size_hint_x=0.7, text=value)
            new_box.add_widget(Widget())
            new_box.add_widget(new_label)
            self.ids.hopper_box.add_widget(new_box)
        self.ids.hopper_box.add_widget(Widget())
        for value in dispensers:
            new_box = BoxLayout(size_hint_y=None, height=31, padding=[0, 0, 0, 1])
            new_label = InfoLabel(size_hint_x=0.7, text=value)
            new_box.add_widget(Widget())
            new_box.add_widget(new_label)
            self.ids.dispenser_box.add_widget(new_box)
        self.ids.pop_up_dispenser.add_widget(Widget())

    def add_hopper_dispenser_widget(self, values):
        for value in values:
            new_box = BoxLayout(size_hint_y=None, height=31, padding=[0, 0, 0, 1])
            new_label = InfoLabel(size_hint_x=0.7, text=value)
            self.ids.pop_up_dispenser.add_widget(new_box)
            new_box.add_widget(Widget())
            new_box.add_widget(new_label)


class FileInfoPopup(Popup):

    def __init__(self, text_field, machine_no, approve_no, pay_in, pay_out, balance_1, balance_2, operation, profit,
                 player_burden, hopper, dispensers, due_date, place, machine, **kwargs):
        super(FileInfoPopup, self).__init__(**kwargs)

        self.set_label_value(text_field, machine_no, approve_no, pay_in, pay_out, balance_1, balance_2, operation,
                             profit, player_burden, hopper, dispensers, due_date, place, machine)

    def set_label_value(self, text_field, machine_no, approve_no, pay_in, pay_out, balance_1, balance_2, operation,
                        profit, player_burden, hopper, dispensers, due_date, place, machine):
        self.ids.pop_up_date.text = due_date
        self.ids.client_place_model.text = place + " | " + machine
        self.ids.file_content.text = text_field
        self.ids.pop_up_machine_no.text = machine_no
        self.ids.pop_up_approve_no.text = approve_no
        self.ids.pop_up_pay_in.text = pay_in
        self.ids.pop_up_pay_out.text = pay_out
        self.ids.pop_up_balance1.text = balance_1
        self.ids.pop_up_balance2.text = balance_2
        self.ids.pop_up_operation.text = operation
        self.ids.pop_up_profit.text = profit
        self.ids.pop_up_player_burden.text = player_burden
        for value in hopper:
            new_box = BoxLayout(size_hint_y=None, height=31, padding=[0, 0, 0, 1])
            new_label = InfoLabel(size_hint_x=0.7, text=value)
            new_box.add_widget(Widget())
            new_box.add_widget(new_label)
            self.ids.hopper_box.add_widget(new_box)
        self.ids.hopper_box.add_widget(Widget())
        for value in dispensers:
            new_box = BoxLayout(size_hint_y=None, height=31, padding=[0, 0, 0, 1])
            new_label = InfoLabel(size_hint_x=0.7, text=value)
            new_box.add_widget(Widget())
            new_box.add_widget(new_label)
            self.ids.dispenser_box.add_widget(new_box)
        self.ids.pop_up_dispenser.add_widget(Widget())

    def add_hopper_dispenser_widget(self, values):
        for value in values:
            new_box = BoxLayout(size_hint_y=None, height=31, padding=[0, 0, 0, 1])
            new_label = InfoLabel(size_hint_x=0.7, text=value)
            self.ids.pop_up_dispenser.add_widget(new_box)
            new_box.add_widget(Widget())
            new_box.add_widget(new_label)


class DataInfo(BoxLayout):
    def __init__(self, date_text, date_info, client_info, **kwargs):
        super(DataInfo, self).__init__(**kwargs)

        self.info_date = date_info
        self.date = date_text
        self.set_widget_values(date_text, date_info, client_info)

    def set_widget_values(self, date_text, date_info, client_info):

        self.ids.selected_date.text = date_text
        if date_info:
            self.ids.client_place_model.text = date_info[0][7] + " | " + date_info[0][8]
        self.ids.selected_client.text = client_info[client_info.find(":") + 1:]
        self.ids.date_info_view.clear_widgets(self.ids.date_info_view.children[:])
        self.ids.date_info_view.add_widget(self.ids.header)

        for i, d_info in enumerate(date_info):
            new_box_layout = BoxLayout(size_hint_y=None, height=30, orientation="horizontal")
            new_box_layout.add_widget(CustomCheckBox(group='check', text=str(i), size_hint=[0.06, 0.1],
                                                     color=[0.0, 0.1, 1.0, 1.0]))
            for j, box_info in enumerate(d_info[:6]):
                button_box = Button()
                if j == 1:
                    button_box.size_hint = [0.14, 0.1]
                elif j == 2:
                    button_box.size_hint = [0.16, 0.1]
                else:
                    button_box.size_hint = [0.12, 0.1]
                if j == 2:
                    button_box.text = box_info.replace(" ", "")
                elif j == 4:
                    button_box.text = box_info.replace("AUSWURF", "").replace("-", "").replace(" ", "")
                else:
                    button_box.text = box_info[box_info.find(":") + 1:]
                new_box_layout.add_widget(button_box)
            self.ids.date_info_view.add_widget(new_box_layout)
        self.ids.date_info_view.add_widget(Widget())

    def display_each_file(self):

        if globals.checked_item == "":
            file_info_popup = WarningPopup("Please check one of the following files.")
            file_info_popup.open()
        else:
            selected_data = self.info_date[int(globals.checked_item)]
            globals.checked_item = ""
            machine_no = selected_data[0][selected_data[0].find(":") + 1:]
            approve_no = selected_data[1][selected_data[1].find(":") + 1:]
            pay_in_amount, pay_out_amount, balance1, balance2, file_content, operation, profit, player_burden = \
                extract_individual_info(content=selected_data)
            hopper_pipe = extract_hopper_dispenser(file_content=file_content,
                                                   main_search_item=["HOPPER", "ROEHRENINHALT"])
            dispenser = extract_hopper_dispenser(file_content=file_content, main_search_item=["DISPENSERINHALT"])
            file_info_popup = FileInfoPopup(text_field=file_content, machine_no=machine_no, approve_no=approve_no,
                                            pay_in=pay_in_amount, pay_out=pay_out_amount, balance_1=balance1,
                                            balance_2=balance2, operation=operation, profit=profit,
                                            player_burden=player_burden, hopper=hopper_pipe, dispensers=dispenser,
                                            due_date=self.date, place=selected_data[7], machine=selected_data[8])
            file_info_popup.open()


class DataCompareInfo(BoxLayout):
    def __init__(self, f_date, s_date, f_info, s_info, **kwargs):
        super(DataCompareInfo, self).__init__(**kwargs)

        self.set_widget_values(f_date=f_date, s_date=s_date, f_date_info=f_info, s_date_info=s_info)

    @staticmethod
    def get_one_date_info(one_date_file):

        total_pay_in = 0
        total_pay_out = 0
        total_balance1 = 0
        total_balance2 = 0
        total_operation = 0
        total_profit = 0
        total_player_burden = 0
        machine_no = ""
        approve_no = ""
        f_file = ""
        for f_data in one_date_file:
            if machine_no == "":
                machine_no = f_data[0][f_data[0].find(":") + 1:]
            if approve_no == "":
                approve_no = f_data[1][f_data[1].find(":") + 1:]

            pay_in, pay_out, balance1, balance2, file_content, operation, profit, player_burden = \
                extract_individual_info(content=f_data)
            total_pay_in += float(pay_in.replace(" ", "").replace(",", "."))
            total_pay_out += float(pay_out.replace(" ", "").replace(",", "."))
            total_balance1 += float(balance1.replace(" ", "").replace(",", "."))
            total_balance2 += float(balance2.replace(" ", "").replace(",", "."))
            total_operation += float(operation.replace(" ", "").replace(",", "."))
            total_profit += float(profit.replace(" ", "").replace(",", "."))
            total_player_burden += float(player_burden.replace(" ", "").replace(",", "."))
            f_file = file_content

        return total_pay_in, total_pay_out, total_balance1, total_balance2, f_file, total_operation, total_profit, \
               total_player_burden, machine_no, approve_no

    def set_widget_values(self, f_date, s_date, f_date_info, s_date_info):

        f_total_pay_in, f_total_pay_out, f_total_balance1, f_total_balance2, f_file, f_total_operation, \
            f_total_profit, f_total_player_burden = extract_individual_info(content=f_date_info)
        s_total_pay_in, s_total_pay_out, s_total_balance1, s_total_balance2, s_file, s_total_operation, \
            s_total_profit, s_total_player_burden = extract_individual_info(content=s_date_info)

        machine_no = f_date_info[0][f_date_info[0].find(":") + 1:]
        approve_no = f_date_info[1][f_date_info[1].find(":") + 1:]
        self.ids.f_selected_date.text = str(f_date)
        self.ids.s_selected_date.text = str(s_date)
        self.ids.client_place_model.text = f_date_info[7] + " | " + f_date_info[8]
        self.ids.f_file_content.text = f_file
        self.ids.s_file_content.text = s_file
        self.ids.compare_machine_no.text = str(machine_no)
        self.ids.compare_approve_no.text = str(approve_no)
        self.ids.compare_pay_in.text = str(round(convert_string_float(str_text=f_total_pay_in) -
                                                 convert_string_float(str_text=s_total_pay_in), 2))
        self.ids.compare_pay_out.text = str(round(convert_string_float(str_text=f_total_pay_out) -
                                                  convert_string_float(str_text=s_total_pay_out), 2))
        self.ids.compare_balance1.text = str(round(convert_string_float(str_text=f_total_balance1) -
                                                   convert_string_float(str_text=s_total_balance1), 2))
        self.ids.compare_balance2.text = str(round(convert_string_float(str_text=f_total_balance2) -
                                                   convert_string_float(str_text=s_total_balance2), 2))
        self.ids.compare_operation.text = str(round(convert_string_float(str_text=f_total_operation) -
                                                    convert_string_float(str_text=s_total_operation), 2))
        self.ids.compare_profit.text = str(round(convert_string_float(str_text=f_total_profit) -
                                                 convert_string_float(str_text=s_total_profit), 2))
        self.ids.compare_player_burden.text = str(round(convert_string_float(str_text=f_total_player_burden) -
                                                        convert_string_float(str_text=s_total_player_burden), 2))


class ReadoutInfo(BoxLayout):
    def __init__(self, **kwargs):
        super(ReadoutInfo, self).__init__(**kwargs)
        self.current_client_thread = None
        self.server_thread = App.get_running_app().server_thread
        self.__init_set_current_client_thread()

    def __init_set_current_client_thread(self):
        client_dict_lists = self.server_thread.client_thread_register_info_list
        client_lists = []
        if client_dict_lists:
            for client_id in client_dict_lists.values():
                client_lists.append(client_id)
            client_device_select = TimeStampDialog(t_s_info=client_lists,
                                                   title="Select one of connected clients")
            client_device_select.bind(on_confirm=partial(self.get_connected_client))
            client_device_select.open()
        else:
            content = Button(text='There is not any connected client.')
            popup = Popup(title='No connected Client', content=content, size_hint=(None, None),
                          size=(500, 100), auto_dismiss=False)
            content.bind(on_press=popup.dismiss)
            popup.open()

    def get_connected_client(self, *args):
        args[0].dismiss()
        current_client_idx = args[1]
        globals.checked_item = ""
        self.current_client_thread = self.server_thread.client_thread[int(current_client_idx)]
        self.ids.client_place_model.text = self.current_client_thread.place_name + " | " + \
                                           self.current_client_thread.model_name

    def communicate_client(self, cmd):
        self.current_client_thread.cmd = cmd
        self.current_client_thread.is_cmd_sent = True
        while self.current_client_thread.is_cmd_sent:
            pass
        file_content = self.current_client_thread.client_content
        self.ids.readout_content.text = file_content.decode('latin_1')

    def save_sd_card(self):
        pass


class InfoLabel(Label):
    def __init__(self, **kwargs):
        super(InfoLabel, self).__init__(**kwargs)


class WarningPopup(Popup):
    label = StringProperty()

    def __init__(self, label, **kwargs):
        super(WarningPopup, self).__init__(**kwargs)
        self.set_description(label)

    def set_description(self, label):
        self.label = label


if __name__ == '__main__':
    DataScreen()
