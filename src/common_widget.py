from kivy.uix.checkbox import CheckBox
from kivy.properties import StringProperty
from utils import globals


class CustomCheckBox(CheckBox):
    text = StringProperty('')

    def on_active(self, instance, value):
        if value:
            globals.checked_item = instance.text
        else:
            globals.checked_item = ""


if __name__ == '__main__':
    CustomCheckBox()
