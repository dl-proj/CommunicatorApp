import os

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from functools import partial
from src.dialog import TimeStampDialog
from utils import globals
from settings import KVS_DIR

Builder.load_file(os.path.join(KVS_DIR, 'data_tool_screen.kv'))


class DataToolScreen(Screen):

    def __init__(self, **kwargs):
        super(DataToolScreen, self).__init__(**kwargs)

    def set_gsg_command(self):
        self.ids.data_tool_info_screen.clear_widgets(self.ids.data_tool_info_screen.children[:])
        self.ids.data_tool_info_screen.add_widget(GSGCommand())

    def set_client_command(self):
        self.ids.data_tool_info_screen.clear_widgets(self.ids.data_tool_info_screen.children[:])
        self.ids.data_tool_info_screen.add_widget(ClientCommand())


class GSGCommand(BoxLayout):

    def __init__(self, **kwargs):
        super(GSGCommand, self).__init__(**kwargs)
        self.current_client_thread = None
        self.server_thread = App.get_running_app().server_thread
        client_dict_lists = self.server_thread.client_thread_register_info_list
        if client_dict_lists:
            client_lists = []
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


class ClientCommand(BoxLayout):

    def __init__(self, **kwargs):
        super(ClientCommand, self).__init__(**kwargs)
        self.current_client_thread = None
        self.server_thread = App.get_running_app().server_thread
        client_dict_lists = self.server_thread.client_thread_register_info_list
        client_lists = []
        for client_id in client_dict_lists.values():
            client_lists.append(client_id)
        client_device_select = TimeStampDialog(t_s_info=client_lists,
                                               title="Select one of connected clients")
        client_device_select.bind(on_confirm=partial(self.get_connected_client))
        client_device_select.open()

    def get_connected_client(self, *args):
        args[0].dismiss()
        current_client_idx = args[1]
        globals.checked_item = ""
        self.current_client_thread = self.server_thread.client_thread[int(current_client_idx)]
        self.ids.client_place_model.text = self.current_client_thread.place_name + " | " + \
                                           self.current_client_thread.model_name


if __name__ == '__main__':

    DataToolScreen()
