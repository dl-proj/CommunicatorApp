import os

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
KVS_DIR = os.path.join(CUR_DIR, 'src', 'kivy_screens')
CONFIG_FILE = os.path.join(CUR_DIR, 'config_server.cfg')
APP_WIDTH = '1920'
APP_HEIGHT = '1080'

SCREEN_DATA = 'data'
SCREEN_ANALYSIS = 'analyze'
SCREEN_OPTIMIZATION = 'optimization'
SCREEN_DATA_TOOL = 'data_tool'
INIT_SCREEN = SCREEN_DATA

GAME_LIST_START_KEY_WORDS = [["SPIELE", "EINSATZ", "GEWINNE"], ["GAMES", "PLAYED", "WON"],
                             ["BLAZING", "STAR", "MG", "BLAZING STAR"], ["40", "THIEVES:", "0"],
                             ["BOOKS", "AND", "PEARLS:", "0"], ["SPIELE", "LEVEL", "ERFOLG"]]
