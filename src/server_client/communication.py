import time
# import cv2
# import numpy as np
import socket
import hashlib
import os
import datetime
import configparser

from threading import Thread
from src.server_client import imagezmq
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from src.db.manager import DatabaseManager
from settings import CONFIG_FILE

Client_Count = 0
Place_Count = 0
Client_list = [[]]
Place_list = []
connection = None
con_AES_key = None


def Padding(s):
    return s + ((16 - len(s) % 16) * '`')


def BPadding(s):
    return s + ((16 - len(s) % 16) * b'`')


def RemovePadding(s):
    return s.replace(b'`', b'')


class ServerThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        params = configparser.ConfigParser()
        params.read(CONFIG_FILE)
        # self.window = window
        # Init params from config file
        self.host = params.get("DEFAULT", "host")
        self.port = params.getint("DEFAULT", "main_port")
        self.video_port1 = params.getint("DEFAULT", "video_port1")
        self.video_port2 = params.getint("DEFAULT", "video_port2")
        self.name = params.get("DEFAULT", "client_name")
        self.cmd_read = params.get("DEFAULT", "command_read")
        self.cmd_reset = params.get("DEFAULT", "command_restart")
        self.save_folder_readout1 = params.get("DEFAULT", "readout1_save_folder")
        self.save_folder_readout2 = params.get("DEFAULT", "readout2_save_folder")

        # Init variables
        self.server = ""
        self.terminate_flag = False

        self.selected_connection = None
        self.selected_place = ""
        self.selected_machine = ""
        self.selected_aes_ek = None
        self.selected_aes_dk = None
        self.command = ""
        self.client_thread = []
        self.client_thread_register_info_list = {}
        self.video_thread1_flag = True
        self.video_thread2_flag = True
        self.client_thread_flag = False

        self.connected_clients_list = []

        # --------------- video streaming thread start ------------------
        # self.video_stream_thread1 = Thread(target=self.receive_video1, args=[])
        # self.video_stream_thread1.daemon = True
        # self.video_stream_thread1.start()
        # ---------------------------------------------------------------

        # --------------- video streaming thread start ------------------
        # self.video_stream_thread2 = Thread(target=self.receive_video2, args=[])
        # self.video_stream_thread2.daemon = True
        # self.video_stream_thread2.start()
        # ---------------------------------------------------------------

        # self.event_handle_thread = Thread(target=self.event_handle)
        # self.event_handle_thread.daemon = True
        # self.event_handle_thread.start()

    # ---------------- video streaming function --------------------
    def receive_video1(self):
        connect = 'tcp://' + self.host + ':' + str(self.video_port1)
        image_hub = imagezmq.ImageHub(connect)
        while True:
            if not self.video_thread1_flag:
                break
            print(" waiting video images from clients ")
            # client_name, jpg_buffer = image_hub.recv_jpg()
            # image = cv2.imdecode(np.frombuffer(jpg_buffer, dtype='uint8'), -1)
            # self.window.show_video(image)
            # image_hub.send_reply(b'OK')
            print("receive one frame!")

    # ----------------------------------------------------------------
    # ---------------- video streaming function --------------------
    def receive_video2(self):
        connect = 'tcp://' + self.host + ':' + str(self.video_port2)
        image_hub = imagezmq.ImageHub(connect)
        while True:
            if not self.video_thread2_flag:
                break
            print(" waiting video images from clients ")
            # client_name, jpg_buffer = image_hub.recv_jpg()
            # image = cv2.imdecode(np.frombuffer(jpg_buffer, dtype='uint8'), -1)
            # self.window.show_video(image)
            # image_hub.send_reply(b'OK')
            print("receive one frame!")

    # ----------------------------------------------------------------

    def create_server(self):
        text = "Initialize server"
        print(text)
        # self.window.change_statue_label(text)

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        print("default timeout: ", self.server.gettimeout())
        text = "Server IP " + self.host + " & PORT " + str(self.port) + " Connection Successful"
        print(text)
        # self.window.change_statue_label(text)

    def accept_clients(self):
        global Client_Count
        global Client_list
        client_cnt = 0
        while True:
            if self.terminate_flag:
                break
            self.server.listen(1)
            (client_connection, address) = self.server.accept()
            print(address)
            self.client_thread.append(ClientThread(self, client_connection, self.save_folder_readout1,
                                                          self.save_folder_readout2))
            self.client_thread[client_cnt].daemon = True
            self.client_thread[client_cnt].start()
            self.client_thread_flag = True
            while not self.client_thread[client_cnt].client_registered_flag:
                pass
            self.client_thread_register_info_list[str(client_cnt)] = self.client_thread[client_cnt].client_registered_id
            print(client_cnt)
            client_cnt += 1

    def run(self):
        self.create_server()
        self.accept_clients()


class ClientThread(Thread):

    def __init__(self, parent, client_connection, save_folder1, save_folder2):
        Thread.__init__(self)
        self.parent = parent
        self.client = client_connection
        # self.window = window
        self.save_folder = save_folder1
        self.save_file_type = ""
        self.read_command_type = 0
        self.save_folder_readout1 = save_folder1
        self.save_folder_readout2 = save_folder2
        self.place_name = ""
        self.machine_name = ""
        self.model_name = ""
        self.check_flag = False
        self.client_thread_flag = True
        self.file_sending_flag = False
        self.client_registered_flag = False
        self.public_key = None
        self.private_key = None
        self.my_hash_public = None
        self.eight_byte = None
        self.session = None
        self.aes_key_d = None
        self.aes_key_e = None
        self.clt_public_key = None
        self.data_buffer = []
        self.client_content = ""
        self.cmd = ""
        self.client_registered_id = ""
        self.is_cmd_sent = False
        self.is_db_received = False

    def generate_key(self):
        random = Random.new().read
        rsa_key = RSA.generate(1024, random)
        self.public_key = rsa_key.publickey().exportKey()
        self.private_key = rsa_key.exportKey()
        self.my_hash_public = hashlib.md5(self.public_key).hexdigest()
        self.eight_byte = os.urandom(8)
        self.session = hashlib.md5(self.eight_byte).hexdigest()
        key_128 = self.eight_byte + self.eight_byte[::-1]
        key_128 = key_128

        self.aes_key_e = AES.new(key_128, AES.MODE_CFB, IV=key_128)
        self.aes_key_d = AES.new(key_128, AES.MODE_CFB, IV=key_128)

    def connection_setup(self):
        global con_AES_key
        global connection
        global Place_Count
        global Place_list
        global Client_Count
        global Client_list

        # get client public key and the hash of it
        recv_msg = self.client.recv(2048)
        split = recv_msg.split(b':')
        tmp_client_public = split[0]
        client_public_hash = split[1]
        tmp_client_public = tmp_client_public.replace(b"\r\n", b'')
        client_public_hash = client_public_hash.replace(b"\r\n", b'').decode()
        tmp_hash_object = hashlib.md5(tmp_client_public)
        tmp_hash = tmp_hash_object.hexdigest()

        if tmp_hash == client_public_hash:
            # sending public key,encrypted eight byte ,hash of eight byte and server public key hash

            while not self.check_flag:
                f_send = self.eight_byte + b':' + self.session.encode() + b':' + self.my_hash_public.encode()

                self.clt_public_key = RSA.importKey(tmp_client_public)
                encrypter = PKCS1_OAEP.new(self.clt_public_key)
                f_send = encrypter.encrypt(f_send)
                print(f_send.__len__())

                # f_send = clientPublic.encrypt(f_send, None)
                self.client.send(f_send + b':' + self.public_key)
                if self.client.recv(2048).decode() == "successed":
                    self.check_flag = True

            recv_msg = self.client.recv(4072)
            if recv_msg.__len__() != 0:
                private_key = RSA.import_key(self.private_key)
                decryptor = PKCS1_OAEP.new(private_key)
                recv_msg = decryptor.decrypt(recv_msg)

                if recv_msg == self.eight_byte:

                    # creating 128 bits key with 16 bytes
                    con_AES_key = self.aes_key_e

                    send_msg = self.aes_key_e.encrypt(Padding("Ready").encode())
                    self.client.send(send_msg)

                    self.register_client_info()

                else:
                    print("Session key from client does not match")
        else:
            print("Public key and public hash doesn't match")
            self.client.close()

    def register_client_info(self):
        reg_info_e = self.client.recv(4072)
        reg_info_d = RemovePadding(self.aes_key_d.decrypt(reg_info_e)).decode()

        info_list = reg_info_d.split(',')

        self.place_name = info_list[0]
        self.machine_name = info_list[1]
        self.model_name = info_list[2]
        self.client_registered_id = info_list[4]
        DatabaseManager().insert_place_db_table(info_list=info_list)
        self.client_registered_flag = True
        # self.window.add_item_event(self.place_name, self.machine_name)
        # self.window.cam_add_item(self.place_name, self.machine_name)
        # self.parent.register_client_connection(self.place_name, self.machine_name, self.client, self.AESKey_e,
        # self.AESKey_d)
        print(self.place_name, self.machine_name, self.client, self.aes_key_e, self.aes_key_d)
        print(" client registered successfully!")

    def receive_file(self):
        text = b''
        while True:
            buffer_e = self.client.recv(2048)
            buffer_d = RemovePadding(self.aes_key_d.decrypt(buffer_e))
            if buffer_d.__len__() < 1020:
                text += buffer_d
                break
            text += buffer_d

        print(text)
        self.file_sending_flag = False

        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)
        current_datetime = datetime.datetime.now()
        readout_time = current_datetime.strftime('%d.%m.%y_%H.%M.%S')
        dir_ = './' + self.save_folder + '/'
        filename = self.machine_name + '_' + readout_time + "." + self.save_file_type
        file_path = os.path.join(dir_, filename)
        file = open(file_path, 'wb')
        file.write(text)
        self.save_info(file_path=file_path)

        # show_thread = Thread(target=self.save_info, args=[file_path])
        # show_thread.daemon = True
        # show_thread.start()

    def receive_readout2_file(self):
        self.save_folder = self.save_folder_readout2
        self.save_file_type = '.ACT'
        self.read_command_type = 2
        self.receive_file()

    def save_info(self, file_path):
        text = ""
        self.data_buffer.clear()
        with open(file_path, 'rb') as f:
            for line in f:
                self.data_buffer.append(line.decode('latin1'))
                text += line.decode('latin1')

        header_list, detail_list = self.extract_info(self.data_buffer)
        print(header_list, detail_list)
        DatabaseManager().insert_client_db_table(cmd_type=self.read_command_type, detail_list=detail_list, text=text,
                                                 machine_name=self.machine_name, place_name=self.place_name)
        print("Receive ACK file from client and save in db successfully!")
        # self.window.remoteview.progress_label.setText(" Ende Auslesungsvorgang!")

    def extract_info(self, buffer):
        self.data_buffer = buffer
        header_info_list = []
        detail_info_list = []
        hersteller_bauart = "Hersteller/Bauart : "
        model = "Model : "
        com_date_time = "Last Communication : "

        for index, ln in enumerate(self.data_buffer):

            if 'K!' in ln:
                hersteller_bauart += self.data_buffer[index + 1].strip().replace(" ", "") + "/"

            if 'K"' in ln:
                model += self.data_buffer[index + 1].strip()
                header_info_list.append(model)

            if 'K$' in ln:
                machineID = self.data_buffer[index + 1].strip().replace(" ", "")
                header_info_list.append(machineID)
                detail_info_list.append(machineID)

            if 'KC' in ln:
                registerID = self.data_buffer[index + 1].strip().replace(" ", "")
                header_info_list.append(registerID)
                detail_info_list.append(registerID)

            if 'K)' in ln:
                hersteller_bauart += self.data_buffer[index + 1].strip().replace(" ", "")
                header_info_list.append(hersteller_bauart)

            if "K'" in ln:
                com_date_time += self.data_buffer[index + 1].strip()
                header_info_list.append(com_date_time)
                detail_info_list.append(self.data_buffer[index + 1].strip())

            if 'KQ' in ln:
                einwurf = self.data_buffer[index + 1].strip()
                detail_info_list.append(einwurf)

            if 'KR' in ln:
                auswurf = self.data_buffer[index + 1].strip()
                detail_info_list.append(auswurf)

            if 'KS' in ln:
                saldo1 = self.data_buffer[index + 1].strip()
                detail_info_list.append(saldo1)

            if 'KJ' in ln:
                break

        return header_info_list, detail_info_list

    def update_config(self):
        data = self.client.recv(2048)
        config_data = RemovePadding(self.aes_key_d.decrypt(data)).decode()
        params = config_data.split(":")
        for param in params:
            if 'host' in param:
                self.window.remoteview.updateconfig.host = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.host_line.setText(self.window.remoteview.updateconfig.host)

            if 'main_port' in param:
                self.window.remoteview.updateconfig.main_port = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.main_port_line.setText(
                    self.window.remoteview.updateconfig.main_port)

            if 'video_port' in param:
                self.window.remoteview.updateconfig.video_port = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.video_port_line.setText(
                    self.window.remoteview.updateconfig.video_port)

            if 'place_name' in param:
                self.window.remoteview.updateconfig.place_name = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.place_line.setText(self.window.remoteview.updateconfig.place_name)

            if 'client_name' in param:
                self.window.remoteview.updateconfig.client_name = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.client_line.setText(self.window.remoteview.updateconfig.client_name)

            if 'machine_id' in param:
                self.window.remoteview.updateconfig.machine_id = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.machine_id_line.setText(
                    self.window.remoteview.updateconfig.machine_id)

            if 'register_id' in param:
                self.window.remoteview.updateconfig.register_id = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.register_id_line.setText(
                    self.window.remoteview.updateconfig.register_id)

            if 'readout1_save_folder' in param:
                self.window.remoteview.updateconfig.save_folder1 = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.save_folder1_line.setText(
                    self.window.remoteview.updateconfig.save_folder1)

            if 'readout2_save_folder' in param:
                self.window.remoteview.updateconfig.save_folder2 = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.save_folder2_line.setText(
                    self.window.remoteview.updateconfig.save_folder2)

            if 'camera_id' in param:
                self.window.remoteview.updateconfig.camera_id = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.camera_id_line.setText(
                    self.window.remoteview.updateconfig.camera_id)

            if 'serial_port' in param:
                self.window.remoteview.updateconfig.serial_port = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.serial_port_line.setText(
                    self.window.remoteview.updateconfig.serial_port)

            if 'readout2_time_val' in param:
                self.window.remoteview.updateconfig.time_val = param.split("=")[1].strip()
                self.window.remoteview.updateconfig.time_val_line.setText(self.window.remoteview.updateconfig.time_val)

        print(config_data)

    def send_data(self):
        time.sleep(0.2)
        cmd = "check running"
        self.client.send(BPadding(cmd.encode()))

    def receive_data(self):
        signal = self.client.recv(4072)
        signal = RemovePadding(self.aes_key_d.decrypt(signal))
        signal = signal.decode()
        if signal == "start file sending":
            self.receive_file()
        elif signal == "start auto file sending":
            self.receive_readout2_file()
        else:
            print(" Client is running... ", signal)

    def send_cmd_to_client(self, cmd):
        text = b''
        self.client.send(BPadding(cmd.encode()))
        signal = self.client.recv(4072)
        signal = RemovePadding(self.aes_key_d.decrypt(signal))
        signal = signal.decode()
        while signal != "start file sending":
            signal = self.client.recv(4072)
            signal = RemovePadding(self.aes_key_d.decrypt(signal))
            signal = signal.decode()
        while True:
            buffer_e = self.client.recv(2048)
            buffer_d = RemovePadding(self.aes_key_d.decrypt(buffer_e))
            if buffer_d.__len__() < 1020:
                text += buffer_d
                break
            text += buffer_d

        return text

    def event_handle(self):
        while True:
            if not self.client_thread_flag:
                break
            try:
                if not self.is_cmd_sent:
                    self.send_data()
                    self.receive_data()
                else:
                    self.client_content = self.send_cmd_to_client(self.cmd)
                    self.is_cmd_sent = False
            except Exception as e:
                print(e)
                text = self.machine_name + " from " + self.place_name + " is disconnected"
                print(text)
                break
            time.sleep(0.5)

    def receive_unsaved_data(self):

        self.read_command_type = 1
        self.save_file_type = "ACK"
        last_date = DatabaseManager().get_last_date()
        cmd = "send unsaved file"
        self.client.send(BPadding(cmd.encode()))
        time.sleep(0.01)
        self.client.send(BPadding(last_date.encode()))
        signal = self.client.recv(4072)
        signal = RemovePadding(self.aes_key_d.decrypt(signal))
        signal = signal.decode()
        while signal == "start file sending":
            self.receive_file()
            self.client.send(BPadding(cmd.encode()))
            signal = self.client.recv(4072)
            signal = RemovePadding(self.aes_key_d.decrypt(signal))
            signal = signal.decode()
        self.is_db_received = True
        print("All client data is saved into the database")

    def run(self):
        self.generate_key()
        self.connection_setup()
        self.receive_unsaved_data()
        self.event_handle()


if __name__ == '__main__':
    # ServerThread().run()
    ClientThread(parent=None, client_connection=None, save_folder1=None, save_folder2=None).save_info(file_path="")
