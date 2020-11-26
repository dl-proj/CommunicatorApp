from utils.datepicker import DatePicker


class CustomDatePicker(DatePicker):

    def __init__(self, **kwargs):
        self.register_event_type('on_confirm')
        super(CustomDatePicker, self).__init__(**kwargs)

    def update_value(self, inst):
        """ Update textinput value on popup close """

        self.text = "%s.%s.%s" % tuple(self.cal.active_date)
        self.dispatch('on_confirm', self.text)

    def on_confirm(self, *args):
        pass


if __name__ == '__main__':
    CustomDatePicker()
