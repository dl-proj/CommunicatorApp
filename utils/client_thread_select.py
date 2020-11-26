# from kivy.app import App
from utils import globals


class ClientThreadSelector:

    def __init__(self, server_thread):
        self.client_thread = None
        self.server_thread = server_thread
        self.client_dict_lists = {}
        self.open_selection()

    def open_selection(self):
        self.client_dict_lists = {"0": "asdf"}

    def get_connected_client(self, *args):
        args[0].dismiss()
        current_client_idx = args[1]
        globals.checked_item = ""
        print(self.client_dict_lists[current_client_idx])
        # self.client_thread = self.server_thread.client_thread[int(current_client_idx)]


if __name__ == '__main__':

    print(ClientThreadSelector(server_thread=None).client_thread)
