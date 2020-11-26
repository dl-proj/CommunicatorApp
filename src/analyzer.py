import os

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.lang import Builder
from functools import partial
from utils.data_tool import modify_date_form, get_top_lost_games, calculate_sum_level_erf, extract_file_info_file_mode
from src.dialog import TimeStampDialog, OpenDialog, LoadDialog
from src.calender import CustomDatePicker
from src.db.manager import DatabaseManager
from utils import globals
from settings import KVS_DIR

Builder.load_file(os.path.join(KVS_DIR, 'analyze_screen.kv'))


class AnalyzerScreen(Screen):

    def __init__(self, **kwargs):
        super(AnalyzerScreen, self).__init__(**kwargs)
        self.date_input = CustomDatePicker()
        self.db_manager = DatabaseManager()
        self.info_date = None
        self.top_lost_ret = None
        self.selected_client = None
        self.kind = None
        self.top_lost_ret = None
        self.registered_client_devices = self.db_manager.read_client_devices()

    def select_method(self, top_lost, kind):
        self.kind = kind
        self.top_lost_ret = top_lost
        working_method = TimeStampDialog(t_s_info=["Select from files", "Select from DB"], title="Select method")
        working_method.bind(on_confirm=partial(self.get_method))
        working_method.open()

    def get_method(self, *args):
        args[0].dismiss()
        selection_method = args[1]
        globals.checked_item = ""
        if selection_method == "0":
            file_browser = LoadDialog()
            file_browser.bind(on_confirm=partial(self.get_selected_file))
            file_browser.open()
        else:
            self.display_top_lost_games()

    def display_top_lost_games(self):
        if self.registered_client_devices:
            client_device_select = TimeStampDialog(t_s_info=self.registered_client_devices,
                                                   title="Select one of registered clients")
            if self.kind == "ratio":
                client_device_select.bind(on_confirm=partial(self.get_selected_client_for_compare))
            else:
                client_device_select.bind(on_confirm=partial(self.get_selected_client))
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
        date = modify_date_form(f_date=args[1])
        self.info_date = self.db_manager.read_only_time_stamp(date=date, client=self.selected_client)
        if self.info_date:
            print(date)
            time_stamp_dialog = TimeStampDialog(t_s_info=self.info_date, title="Select time stamp")
            time_stamp_dialog.bind(on_confirm=partial(self.get_time_stamp))
            time_stamp_dialog.open()

    def get_time_stamp(self, *args):
        args[0].dismiss()
        time_stamp = self.info_date[int(args[1])]
        time_stamp_info = self.db_manager.read_time_stamp_file(time_stamp_date=time_stamp)
        self.ids.analyze_info_screen.clear_widgets(self.ids.analyze_info_screen.children[:])
        self.ids.analyze_info_screen.add_widget(TopLostGamesInfo(top_lost_date=time_stamp,
                                                                 top_lost_info=time_stamp_info,
                                                                 top_lost=self.top_lost_ret,
                                                                 client=self.selected_client))

    def get_selected_client_for_compare(self, *args):
        args[0].dismiss()
        self.selected_client = self.registered_client_devices[int(args[1])]
        globals.checked_item = ""
        two_dates_input = OpenDialog(time_stamp_ret=False, client=None)
        two_dates_input.bind(on_confirm=partial(self.get_info_two_dates))
        two_dates_input.open()

    def get_info_two_dates(self, *args):
        args[0].dismiss()
        first_com_date = modify_date_form(f_date=args[1])
        second_com_date = modify_date_form(f_date=args[2])
        from_to_info = self.db_manager.read_between_two_dates(f_date_str=first_com_date, s_date_str=second_com_date,
                                                              client=self.selected_client)
        self.ids.analyze_info_screen.clear_widgets(self.ids.analyze_info_screen.children[:])
        self.ids.analyze_info_screen.add_widget(PaymentRatio(f_date=first_com_date, s_date=second_com_date,
                                                             f_t_info=from_to_info, client=self.selected_client))

    def get_selected_file(self, *args):
        args[0].dismiss()
        file_path = args[1]
        file_name = args[2][0]
        file_full_path = os.path.join(file_path, file_name)
        selected_data = extract_file_info_file_mode(full_path=file_full_path)
        self.ids.analyze_info_screen.clear_widgets(self.ids.analyze_info_screen.children[:])
        if self.kind == "ratio":
            ratio_date = selected_data[2][:selected_data[2].find(":") - 3].replace(" ", "")
            self.ids.analyze_info_screen.add_widget(PaymentRatio(f_date=ratio_date, s_date=ratio_date,
                                                                 f_t_info=[selected_data], client=selected_data[1]))
        else:
            self.ids.analyze_info_screen.add_widget(TopLostGamesInfo(top_lost_date=selected_data[2],
                                                                     top_lost_info=selected_data,
                                                                     top_lost=self.top_lost_ret,
                                                                     client=selected_data[1]))


class TopLostGamesInfo(BoxLayout):

    def __init__(self, top_lost_date, top_lost_info, top_lost, client, **kwargs):
        super(TopLostGamesInfo, self).__init__(**kwargs)
        self.date_input = CustomDatePicker()
        self.db_manager = DatabaseManager()
        self.top_lost = top_lost
        self.t_l_date = top_lost_date
        self.t_l_info = top_lost_info
        self.info_date = None
        self.client = client
        self.set_widget()

    def set_label_texts(self, game_content):

        if len(game_content) > 1:
            self.ids.game_1_title.text = "1." + game_content[0][0]
            self.ids.game_2_title.text = "2." + game_content[1][0]
            self.ids.game_1.text = str(game_content[0][3])
            self.ids.game_2.text = str(game_content[1][3])
        if len(game_content) > 2:
            self.ids.game_3_title.text = "3." + game_content[2][0]
            self.ids.game_3.text = str(game_content[2][3])
        if len(game_content) > 3:
            self.ids.game_4_title.text = "4." + game_content[3][0]
            self.ids.game_4.text = str(game_content[3][3])
        if len(game_content) > 4:
            self.ids.game_5_title.text = "5." + game_content[4][0]
            self.ids.game_5.text = str(game_content[4][3])
        if len(game_content) > 5:
            self.ids.game_6_title.text = "6." + game_content[5][0]
            self.ids.game_6.text = str(game_content[5][3])
        if len(game_content) > 6:
            self.ids.game_7_title.text = "7." + game_content[6][0]
            self.ids.game_7.text = str(game_content[6][3])
        if len(game_content) > 7:
            self.ids.game_8_title.text = "8." + game_content[7][0]
            self.ids.game_8.text = str(game_content[7][3])
        if len(game_content) > 8:
            self.ids.game_9_title.text = "9." + game_content[8][0]
            self.ids.game_9.text = str(game_content[8][3])
        if len(game_content) > 9:
            self.ids.game_10_title.text = "10." + game_content[9][0]
            self.ids.game_10.text = str(game_content[9][3])

        return

    def set_widget(self):

        self.ids.game_selected_date.text = self.t_l_date
        self.ids.game_selected_client.text = self.client[self.client.find(":") + 1:]
        self.ids.client_place_model.text = self.t_l_info[7] + " | " + self.t_l_info[8]
        file_content = self.t_l_info[6]
        self.ids.game_file_content.text = file_content
        top_games, lost_games = get_top_lost_games(file_content=file_content)
        if self.top_lost == "top":
            if top_games:
                sorted_top_games = sorted(top_games, key=lambda x: x[3], reverse=True)
                self.set_label_texts(game_content=sorted_top_games)
        else:
            if lost_games:
                sorted_lost_games = sorted(lost_games, key=lambda x: x[3])
                self.set_label_texts(game_content=sorted_lost_games)

    def select_method(self):
        working_method = TimeStampDialog(t_s_info=["Select from files", "Select from DB"], title="Select method")
        working_method.bind(on_confirm=partial(self.get_method))
        working_method.open()

    def get_method(self, *args):
        args[0].dismiss()
        selection_method = args[1]
        globals.checked_item = ""
        if selection_method == "0":
            file_browser = LoadDialog()
            file_browser.bind(on_confirm=partial(self.get_selected_file))
            file_browser.open()
        else:
            self.display_date()

    def get_selected_file(self, *args):
        args[0].dismiss()
        file_path = args[1]
        file_name = args[2][0]
        file_full_path = os.path.join(file_path, file_name)
        selected_data = extract_file_info_file_mode(full_path=file_full_path)
        self.t_l_date = selected_data[2]
        self.t_l_info = selected_data
        self.client = selected_data[1]
        self.set_widget()

    def display_date(self):
        self.date_input.show_popup(1, 0.3)
        self.date_input.bind(on_confirm=self.get_date)

    def get_date(self, *args):
        date = modify_date_form(f_date=args[1])
        print(date)
        self.info_date = self.db_manager.read_only_time_stamp(date=date, client=self.client)
        if self.info_date:
            time_stamp_dialog = TimeStampDialog(t_s_info=self.info_date, title="Select time stamp")
            time_stamp_dialog.bind(on_confirm=partial(self.get_time_stamp))
            time_stamp_dialog.open()
        else:
            content = Button(text='There is not any saved data with the selected date.')
            popup = Popup(title='No Data', content=content, size_hint=(None, None),
                          size=(500, 100), auto_dismiss=False)
            content.bind(on_press=popup.dismiss)
            popup.open()

    def get_time_stamp(self, *args):
        args[0].dismiss()
        self.t_l_date = self.info_date[int(args[1])]
        self.t_l_info = self.db_manager.read_time_stamp_file(time_stamp_date=self.t_l_date)
        self.set_widget()


class PaymentRatio(BoxLayout):

    def __init__(self, f_date, s_date, f_t_info, client, **kwargs):
        super(PaymentRatio, self).__init__(**kwargs)
        self.client = client
        self.set_widgets(f_date=f_date, s_date=s_date, f_t_info=f_t_info)

    def set_widgets(self, f_date, s_date, f_t_info):

        self.ids.von_selected_date.text = f_date
        self.ids.bis_selected_date.text = s_date
        if f_t_info:
            self.ids.client_place_model.text = f_t_info[0][7] + " | " + f_t_info[0][8]
        self.ids.game_selected_client.text = self.client[self.client.find(":") + 1:]
        top_total_level = 0
        top_total_erf = 0
        lost_total_level = 0
        lost_total_erf = 0
        for d_f_t_info in f_t_info:
            file_content = d_f_t_info[6]
            d_top_games, d_lost_games = get_top_lost_games(file_content=file_content)
            top_total_level, top_total_erf = calculate_sum_level_erf(games=d_top_games,
                                                                          total_level=top_total_level,
                                                                          total_erf=top_total_erf)
            lost_total_level, lost_total_erf = calculate_sum_level_erf(games=d_lost_games,
                                                                            total_level=lost_total_level,
                                                                            total_erf=lost_total_erf)

        if f_t_info:
            top_ratio = round((top_total_level - top_total_erf) * 100 / top_total_level, 2)
            lost_ratio = round((lost_total_level - lost_total_erf) * 100 / lost_total_level, 2)
            diff_ratio = round(top_ratio + lost_ratio, 2)
            self.ids.top_game_ratio.text = str(top_ratio) + "%"
            self.ids.lost_game_ratio.text = str(lost_ratio) + "%"
            self.ids.total_game_ratio.text = str(diff_ratio) + "%"


if __name__ == '__main__':
    AnalyzerScreen()
