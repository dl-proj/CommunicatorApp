import datetime

from utils.folder_file_manager import load_text
from settings import GAME_LIST_START_KEY_WORDS


def extract_individual_info(content):
    pay_in_amount = content[3][content[3].find(":") + 1:]
    pay_out_amount = content[4].replace("AUSWURF", "").replace("-", "").replace(" ", "")
    balance1 = content[5][content[5].find(":") + 1:]
    file_content = content[6]
    balance2 = extract_item_file(file_content=file_content, main_search_item="SALDO (2)",
                                 sub_search_items=[":"])[0]
    operation = extract_item_file(file_content=file_content, main_search_item="EINSAETZE",
                                  sub_search_items=[":"])[0]
    profit = extract_item_file(file_content=file_content, main_search_item="GEWINNE",
                               sub_search_items=["-"])[0]
    player_burden = extract_item_file(file_content=file_content, main_search_item="SPIELERAUFWAND",
                                      sub_search_items=[":"])[0]

    return pay_in_amount, pay_out_amount, balance1, balance2, file_content, operation, profit, player_burden


def extract_item_file(file_content, main_search_item, sub_search_items):
    prices = []
    main_index = file_content.find(main_search_item)
    sub_content = file_content[main_index + len(main_search_item) + 1:]
    for sub_item in sub_search_items:
        price_info = ""
        sub_index = sub_content.find(sub_item)
        if sub_index > 30 or sub_index == -1:
            continue
        cnt = sub_index + len(sub_item) + 1
        while sub_content[cnt] != ",":
            price_info += sub_content[cnt]
            cnt += 1
        price_info += sub_content[cnt] + sub_content[cnt + 1] + sub_content[cnt + 2]
        sub_content = sub_content[cnt + 3:]
        if len(sub_item) > 1:
            prices.append(sub_item + price_info.replace(" ", ""))
        else:
            prices.append(price_info.replace(" ", ""))

    return prices


def extract_hopper_dispenser(file_content, main_search_item):
    prices = []
    content_lists = file_content.split("\n")
    for i, c_list in enumerate(content_lists):
        ret = False
        for item in main_search_item:
            if item in c_list:
                ret = True
                break
        if ret:
            i += 1
            c_list = content_lists[i]
            c_list_content = c_list.replace(" ", "")
            while c_list_content != "" and "==" not in c_list_content:
                if "K" not in c_list_content:
                    prices.append(c_list)
                i += 1
                c_list = content_lists[i]
                c_list_content = c_list.replace(" ", "")
            break

    return prices


def replace_date(date_str):
    if len(date_str) == 1:
        return "0" + date_str
    else:
        return date_str


def modify_date_form(f_date):
    first_pt = f_date.find(".")
    second_pt = f_date.rfind(".")
    day = f_date[:first_pt]
    month = f_date[first_pt + 1:second_pt]
    year = f_date[second_pt + 1:]
    day = replace_date(date_str=day)
    month = replace_date(date_str=month)
    m_date = day + "." + month + "." + year

    return m_date


def convert_string_float(str_text):
    return float(str_text.replace(" ", "").replace(",", "."))


def get_top_lost_games(file_content):
    top_games = []
    lost_games = []
    file_list = file_content.split("\n")

    for i, t_l_list in enumerate(file_list):
        start_ret = False
        for game_start_index in GAME_LIST_START_KEY_WORDS:
            index_cnt = 0
            for index_word in game_start_index:
                if index_word in t_l_list:
                    index_cnt += 1
            if index_cnt == len(game_start_index):
                start_ret = True
                break
        if start_ret:
            line_index = i + 1
            line_info = file_list[line_index]
            line_ret = estimate_game_list_line(line=line_info)
            while line_ret != "break":
                if line_ret == "game":
                    real_values = []
                    init_values = line_info.split(" ")
                    for i_value in init_values:
                        if i_value == "":
                            continue
                        real_values.append(i_value)
                    level = int(real_values[1])
                    erf = int(real_values[2])
                    if level - erf > 0:
                        top_games.append([file_list[line_index - 1], level, erf, level - erf])
                    elif level - erf < 0:
                        lost_games.append([file_list[line_index - 1], level, erf, level - erf])

                line_index += 1
                line_info = file_list[line_index]
                line_ret = estimate_game_list_line(line=line_info)
            break

    return top_games, lost_games


def estimate_game_list_line(line):
    line = line.replace(" ", "")
    if is_number(line):
        if line == "77777":
            ret = "skip"
        else:
            ret = "game"
    else:
        name_ret = False
        for character in line:
            if character.isalpha():
                name_ret = True
                break
        if name_ret:
            ret = "skip"
        else:
            ret = "break"

    return ret


def is_number(n):
    try:
        float(n)
    except ValueError:
        return False
    return True


def convert_str_to_date(str_date):
    first_pt = str_date.find(".")
    day = str_date[:first_pt]
    month = str_date[first_pt + 1:first_pt + 3]
    year = str_date[first_pt + 4:first_pt + 8]
    day = replace_date(date_str=day)
    month = replace_date(date_str=month)
    date = datetime.date(int(year), int(month), int(day))

    return date


def calculate_sum_level_erf(games, total_level, total_erf):
    for game in games:
        total_level += game[1]
        total_erf += game[2]

    return total_level, total_erf


def extract_file_info_file_mode(full_path):
    with open(full_path, encoding='latin1') as f:
        file_content = f.read()
    file_list = file_content.split("\n")
    file_date = ""
    model_no = ""
    place_no = ""
    machine_no = ""
    license_no = ""
    pay_in = ""
    pay_out = ""
    balance = ""
    for i, f_list in enumerate(file_list):
        if "K'" in f_list:
            if file_date == "":
                file_date = file_list[i + 1]
        if 'K"' in f_list:
            if model_no == "":
                model_no = file_list[i + 1]
        if "K#" in f_list:
            if place_no == "":
                place_no = file_list[i + 1]
        if "K$" in f_list:
            if machine_no == "":
                machine_no = file_list[i + 1]
        if "KC" in f_list:
            if license_no == "":
                license_no = file_list[i + 1]
        if "KQ" in f_list:
            if pay_in == "":
                pay_in = file_list[i + 1]
        if "KR" in f_list:
            if pay_out == "":
                pay_out = file_list[i + 1]
        if "KS" in f_list:
            if balance == "":
                balance = file_list[i + 1]

    new_data = [machine_no, license_no, file_date, pay_in, pay_out, balance, file_content, place_no, model_no]

    return new_data


if __name__ == '__main__':
    get_top_lost_games(file_content=load_text(filename=""))
