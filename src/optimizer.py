import os

from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from functools import partial
from src.dialog import OpenDialog, TimeStampDialog
from src.db.manager import DatabaseManager
from utils.data_tool import modify_date_form, get_top_lost_games, calculate_sum_level_erf
from utils import globals
from settings import KVS_DIR

Builder.load_file(os.path.join(KVS_DIR, 'optimization_screen.kv'))


class OptimizeScreen(Screen):

    def __init__(self, **kwargs):
        super(OptimizeScreen, self).__init__(**kwargs)
        self.db_manager = DatabaseManager()
        self.registered_client_devices = self.db_manager.read_client_devices()
        self.selected_client = None

    def display_ratio_bar(self):
        if self.registered_client_devices:
            client_device_select = TimeStampDialog(t_s_info=self.registered_client_devices,
                                                   title="Select one of registered clients")
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
        two_dates_input = OpenDialog(time_stamp_ret=False, client=self.selected_client)
        two_dates_input.bind(on_confirm=partial(self.get_info_two_dates))
        two_dates_input.open()

    def get_info_two_dates(self, *args):

        args[0].dismiss()
        top_total_level = 0
        top_total_erf = 0
        lost_total_level = 0
        lost_total_erf = 0
        first_com_date = modify_date_form(f_date=args[1])
        second_com_date = modify_date_form(f_date=args[2])
        from_to_info = self.db_manager.read_between_two_dates(f_date_str=first_com_date, s_date_str=second_com_date,
                                                              client=self.selected_client)
        self.ids.von_selected_date.text = first_com_date
        self.ids.bis_selected_date.text = second_com_date
        self.ids.opt_selected_client.text = self.selected_client[self.selected_client.find(":") + 1:]
        if from_to_info:
            self.ids.client_place_model.text = from_to_info[0][7] + " | " + from_to_info[0][8]
        for d_f_t_info in from_to_info:
            file_content = d_f_t_info[6]
            d_top_games, d_lost_games = get_top_lost_games(file_content=file_content)
            top_total_level, top_total_erf = calculate_sum_level_erf(games=d_top_games,
                                                                          total_level=top_total_level,
                                                                          total_erf=top_total_erf)
            lost_total_level, lost_total_erf = calculate_sum_level_erf(games=d_lost_games,
                                                                            total_level=lost_total_level,
                                                                            total_erf=lost_total_erf)
        if from_to_info:
            top_ratio = round((top_total_level - top_total_erf) * 100 / top_total_level, 0)
            lost_ratio = round((lost_total_level - lost_total_erf) * 100 / lost_total_level, 0)


if __name__ == '__main__':
    OptimizeScreen()
