import os
import threading
import time

from kivy.core.window import Window
from kivy.config import Config
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from src.server_client.communication import ServerThread
from settings import APP_WIDTH, APP_HEIGHT
from src.data import DataScreen
from src.analyzer import AnalyzerScreen
from src.optimizer import OptimizeScreen
from src.data_tool import DataToolScreen
from settings import SCREEN_ANALYSIS, SCREEN_DATA, SCREEN_OPTIMIZATION, INIT_SCREEN, SCREEN_DATA_TOOL

Config.read(os.path.expanduser('~/.kivy/config.ini'))
Config.set('graphics', 'resizeable', '0')
Config.set('graphics', 'width', str(APP_WIDTH))
Config.set('graphics', 'height', str(APP_HEIGHT))
Config.set('kivy', 'keyboard_mode', 'system')
Config.set('graphics', 'keyboard_mode', 'en_US')
Config.set('graphics', 'log_level', 'info')

Config.write()
Window.size = (int(APP_WIDTH), int(APP_HEIGHT))


class VdaiTool(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.is_stop = False
        self.server_thread = ServerThread()
        self.server_thread.daemon = True
        self.server_thread.start()
        self.server_client_connection_thread = threading.Thread(target=self.manage_client_connection_status, args=[])
        self.server_client_connection_thread.start()
        self.pop_up_thread = None
        self.data_screen = DataScreen(name=SCREEN_DATA)
        self.analysis_screen = AnalyzerScreen(name=SCREEN_ANALYSIS)
        self.optimization_screen = OptimizeScreen(name=SCREEN_OPTIMIZATION)
        self.data_tool_screen = DataToolScreen(name=SCREEN_DATA_TOOL)
        screens = [
            self.data_screen,
            self.analysis_screen,
            self.optimization_screen,
            self.data_tool_screen
        ]

        self.sm = ScreenManager()
        for screen in screens:
            self.sm.add_widget(screen)

    def build(self):

        self.sm.current = INIT_SCREEN
        return self.sm

    def manage_client_connection_status(self):

        known_clients = []
        while True:
            time.sleep(1)
            if self.is_stop:
                break
            for client_id in self.server_thread.client_thread_register_info_list.keys():
                client_name = self.server_thread.client_thread_register_info_list[client_id]
                if client_name not in known_clients:
                    while not self.server_thread.client_thread[int(client_id)].is_db_received:
                        if self.is_stop:
                            break
                        pass
                    known_clients.append(client_name)
                    self.pop_up_thread = threading.Thread(target=self.show_pop_up, args=[client_name, ])
                    self.pop_up_thread.start()

    @staticmethod
    def show_pop_up(client_name):
        content = Button(text='Server received all the unsaved data from {}.'.format(client_name))
        popup = Popup(title='A Client Device connected', content=content, size_hint=(None, None),
                      size=(500, 100), auto_dismiss=False)
        content.bind(on_press=popup.dismiss)
        popup.open()

    @staticmethod
    def get_id(instance):
        for _id, widget in instance.parent.ids.items():
            if widget.__self__ == instance:
                return _id

    def on_stop(self):
        self.is_stop = True
        self.server_thread.terminate_flag = False
        self.server_thread.video_thread2_flag = False
        self.server_thread.video_thread1_flag = False
        for client_id in self.server_thread.client_thread_register_info_list.keys():
            self.server_thread.client_thread[int(client_id)].client_thread_flag = False
            self.server_thread.client_thread[int(client_id)].join()
        self.pop_up_thread.join()
        self.server_thread.video_stream_thread1.join()
        self.server_thread.video_stream_thread2.join()
        self.server_thread.join()
        Window.close()


if __name__ == '__main__':
    VdaiTool().run()
