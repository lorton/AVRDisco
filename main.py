"""
Main file for the app, all non-database application logic lives here.
"""

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from datetime import datetime
from kivymd.uix.list import TwoLineAvatarIconListItem, ILeftBodyTouch
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.utils import platform

from telnetlib import Telnet

PORT = '23'

if platform == "android":
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])


from database import Database

# Initialize db instance
db = Database()


class AddActionDialogContent(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class SettingsDialogContent(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MainApp(MDApp):

    def __init__(self):
        MDApp.__init__(self)
        self.delete_mode = False
        self.task_list_dialog = None
        self.settings_dialog = None
        self.confirm_dialog = None


    def build(self):
        # Setting theme to my favorite theme
        self.theme_cls.primary_palette = "DeepPurple"

    def show_settings_dialog(self):
        if not self.settings_dialog:
            self.settings_dialog = MDDialog(
                title="Settings",
                type="custom",
                content_cls=SettingsDialogContent())

        self.settings_dialog.open()

    def show_task_dialog(self):
        if not self.task_list_dialog:
            self.task_list_dialog = MDDialog(
                title="Add Receiver Command",
                type="custom",
                content_cls=AddActionDialogContent())

        self.task_list_dialog.open()

    def start_delete_mode(self):
        self.delete_mode = True

    def on_start(self):
        """Load actions from the database"""
        try:
            actions = db.get_actions()

        except Exception as e:
            print("Loading database failed")
            print(e)
            return

        try:
            teln = Telnet(db.get_ip(), PORT)
        except Exception as e:
            print(e)
            self.show_settings_dialog()
            self.settings_dialog.bind(on_dismiss=lambda x: self.on_start())
            return

        self.update_receiver_status()

        for a in actions:
            rowid, label, action = a
            self.add_action(label, action, add_to_db=False)

    def update_receiver_status(self):
        status = self.get_receiver_status()
        self.root.ids['receiver_status'].text = status


    def get_main_status(self):
        """
        This function is embarrassing in terms of readability, but it works.
        """

        self.send_action("MU?")
        self.send_action("MV?")
        response = self.read_all_responses().split("\r")
        if len(response) < 4:  # Bad response, try again
            return self.get_main_status()

        new_response = response[-4:]
        main_power = new_response[0]
        volume_split = new_response[1:]
        volume = volume_split[0][2:]
        if len(volume) > 2:
            volume = volume[:2] + "." + volume[2:]
        max_volume = volume_split[1].split(" ")[-1]
        return f"{main_power} {volume}/{max_volume}"

    def get_zone2_status(self):
        """
        This function also is embarrassing in terms of readability, but it works.
        """

        self.send_action("Z2?")
        response = self.read_all_responses().split("\r")
        if len(response) < 4:
            return self.get_zone2_status()
        zone2_vol = response[2][2:]

        self.send_action("Z2MU?")
        response = self.read_all_responses().split("\r")
        zone2_mu = response[0]

        return f"{zone2_mu} {zone2_vol}"


    def get_receiver_status(self):

        main_status = self.get_main_status()
        zone2_status = self.get_zone2_status()

        return f"{main_status} {zone2_status}"

    def close_settings(self, *args):
        self.settings_dialog.dismiss()

    def close_dialog(self, *args):
        self.task_list_dialog.dismiss()

    def set_ip(self, ip):
        db.set_ip(ip)

    def process_delete_click(self, action):
        """ Delete click from the floating delete button opens a dialog """
        delete_button = MDFlatButton(
            text="DELETE",
            theme_text_color="Custom",
            text_color=self.theme_cls.primary_color,
            on_release=lambda btn,x=action: self.confirmed_delete(x))
        discard_button = MDFlatButton(
            text="DISCARD",
            theme_text_color="Custom",
            text_color=self.theme_cls.primary_color,)
        self.confirm_dialog = MDDialog(
            text= f"Delete '{action}' Button?",
            buttons=[discard_button, delete_button])
        discard_button.bind(on_release=self.confirm_dialog.dismiss)

        self.confirm_dialog.open()

    def reset_widgets(self):
        """ Clear all buttons and reload from DB via on start """
        self.root.ids['container'].clear_widgets()
        self.on_start()

    def confirmed_delete(self, action):
        """
        After you've entered delete mode and clicked a button, confirm and
        delete
        """
        db.delete_action(action)
        self.reset_widgets()
        self.confirm_dialog.dismiss()
        self.confirm_dialog = None
        self.delete_mode = False

    def process_click(self, action):
        """ If you're deleting, open dialog, otherwise process action """
        if self.delete_mode:
            self.process_delete_click(action)
        else:
            self.send_action(action)
            self.update_receiver_status()

    def send_action(self, action):
        """ Send action to the db-stored IP address """
        with Telnet(db.get_ip(), PORT) as tn:
            tn.write(action.encode('ascii'))

    def read_all_responses(self):
        """ Get all data from the telnet read buffer and return it """
        with Telnet(db.get_ip(), PORT) as tn:
            total_response = ""
            while True:
                response = tn.read_until(b'\r', timeout=0.1)
                if response == b'':
                    break
                total_response += response.decode('ascii')

        return total_response


    def add_action(self, label, action, add_to_db=True):
        """ Add an action to the database and create its button """
        if add_to_db:
            db.create_action(label, action)

        button = MDRaisedButton(text=str(label), size_hint=(1, 1))
        button.on_release = lambda x=action: self.process_click(x)

        self.root.ids['container'].add_widget(button)

if __name__ == '__main__':
    app = MainApp()
    app.run()
