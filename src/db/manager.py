import sqlite3
import configparser
import datetime

from utils.data_tool import convert_str_to_date, replace_date
from settings import CONFIG_FILE


class DatabaseManager:

    def __init__(self):
        params = configparser.ConfigParser()
        params.read(CONFIG_FILE)
        self.connect = sqlite3.connect(params.get("DEFAULT", "db_file"))
        self.cursor = self.connect.cursor()

    def read_whole_info_date(self, date, client):
        sql_cmd = "SELECT machine_id, register_id, datetime, einwurf, auswurf, saldo1, ack_file, place, machine " \
                  "FROM client_db_table WHERE register_id = ? and datetime like ?"
        self.cursor.execute(sql_cmd, (client, '%' + date + '%',))
        info = self.cursor.fetchall()

        return info

    def read_only_time_stamp(self, date, client):
        sql_cmd = "SELECT datetime FROM client_db_table WHERE register_id = ? and datetime like ?"
        self.cursor.execute(sql_cmd, (client, '%' + date + '%',))
        info = self.cursor.fetchall()
        list_info = []
        for d_info in info:
            if d_info[0] not in list_info:
                list_info.append(d_info[0])

        return list_info

    def read_time_stamp_file(self, time_stamp_date):

        sql_cmd = "SELECT machine_id, register_id, datetime, einwurf, auswurf, saldo1, ack_file, place, machine " \
                  "FROM client_db_table WHERE datetime = ?"
        self.cursor.execute(sql_cmd, (time_stamp_date,))
        info = self.cursor.fetchone()

        return info

    def read_between_two_dates(self, f_date_str, s_date_str, client):

        bet_info = []
        f_date = convert_str_to_date(str_date=f_date_str)
        s_date = convert_str_to_date(str_date=s_date_str)
        sql_cmd = "SELECT machine_id, register_id, datetime, einwurf, auswurf, saldo1, ack_file, place, machine " \
                  "FROM client_db_table where register_id = ?"
        self.cursor.execute(sql_cmd, (client, ))
        info = self.cursor.fetchall()
        for d_info in info:
            d_date_str = d_info[2]
            d_date = convert_str_to_date(str_date=d_date_str)
            if f_date <= d_date <= s_date:
                bet_info.append(d_info)

        return bet_info

    def read_client_devices(self):
        sql_cmd = "SELECT register_id FROM client_db_table"
        self.cursor.execute(sql_cmd)
        info = self.cursor.fetchall()
        list_info = []
        for d_info in info:
            if d_info[0] not in list_info:
                list_info.append(d_info[0])

        return list_info

    def get_last_date(self):
        sql_cmd = "SELECT datetime FROM client_db_table "
        self.cursor.execute(sql_cmd)
        str_date_list = self.cursor.fetchall()
        d_dates = []
        modified_dates = []
        for str_date in str_date_list:
            str_date = str_date[0]
            init_date = str_date[str_date.find(".") - 2:]
            split_date = init_date.split(" ")
            s_date = split_date[0]
            first_pt = s_date.find(".")
            second_pt = s_date.rfind(".")
            day = s_date[:first_pt]
            month = s_date[first_pt + 1:second_pt]
            year = s_date[second_pt + 1:]
            day = replace_date(date_str=day)
            month = replace_date(date_str=month)
            if len(year) == 2:
                year = "20" + year
            time_pt = str_date.find(":")
            hour = str_date[time_pt - 2:time_pt]
            minu = str_date[time_pt + 1:time_pt + 3]
            modified_dates.append(day + "." + month + "." + year + " " + hour + ":" + minu)
            d_dates.append(datetime.datetime.strptime(year + "/" + month + "/" + day + " " + hour + ":" + minu,
                                                      "%Y/%m/%d %H:%M"))
        if not d_dates:
            last_date = "00.00.00  00:00"
        else:
            last_date = modified_dates[d_dates.index(max(d_dates))]

        return last_date

    def insert_place_db_table(self, info_list):
        sql_place_insert_query = "INSERT INTO place_db_table (place, machine, model, machine_id, register_id, " \
                                 "hersteller_bauart, datetime, statue) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        place_insert_tuple = (
            info_list[0], info_list[1], info_list[2], info_list[3], info_list[4], info_list[5], info_list[6], "online")
        self.cursor.execute(sql_place_insert_query, place_insert_tuple)
        self.connect.commit()
        self.connect.close()

    def insert_client_db_table(self, cmd_type, place_name, machine_name, detail_list, text):

        init_date = detail_list[1][detail_list[1].find(".") - 2:]
        split_date = init_date.split(" ")
        s_date = split_date[0]
        s_date_len = len(s_date)
        s_year_index = s_date.rfind(".")
        s_year = s_date[s_year_index + 1:]
        s_month_date = s_date[:s_year_index + 1]
        if len(s_year) == 4:
            s_year = s_year[2:]
        s_date = s_month_date + s_year
        detail_list[1] = s_date + init_date[s_date_len:]

        sql_client_insert_query = ""
        if cmd_type == 1:
            sql_client_insert_query = " INSERT INTO client_db_table (place, machine, machine_id, register_id, " \
                                      "datetime, einwurf, auswurf, saldo1, ack_file) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        if cmd_type == 2:
            sql_client_insert_query = " INSERT INTO client_db_table1 (place, machine, machine_id, register_id, " \
                                      "datetime, einwurf, auswurf, saldo1, ack_file) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        client_insert_tuple = (place_name, machine_name, detail_list[0], detail_list[1], detail_list[2], detail_list[3],
                               detail_list[4], detail_list[5], text)
        self.cursor.execute(sql_client_insert_query, client_insert_tuple)
        self.connect.commit()
        self.connect.close()


if __name__ == '__main__':
    DatabaseManager().read_client_devices()
