"""
Database class for the application
There is a very small table for persistant settings (IP address), and a 
table for the actions. The actions table has a label and an action
"""

import sqlite3
import os

class Database:
    def __init__(self):
        self.con = sqlite3.connect('action.db')
        self.cursor = self.con.cursor()
        self.create_action_table()

    def create_action_table(self):
        """
        Create actions table, if it's empty, add a bunch of default buttons
        """
        self.cursor.execute("CREATE TABLE IF NOT EXISTS actions(id integer PRIMARY KEY AUTOINCREMENT, label varchar(50) NOT NULL, action varchar(50) NOT NULL)")

        if len(self.get_actions()) == 0:
            # Row 1
            self.create_action("Volume 40", "MV40")
            self.create_action("Volume 55", "MV55")
            self.create_action("Volume 70", "MV70")

            # Row 2
            self.create_action("Volume Up", "MVUP\nMVUP")
            self.create_action("Volume Up+", "MVUP\nMVUP\nMVUP\nMVUP\nMVUP")
            self.create_action("Mute", "MUON")

            # Row 3
            self.create_action("Volume Down", "MVDOWN\nMVDOWN")
            self.create_action("Volume Down-", "MVDOWN\nMVDOWN\nMVDOWN\nMVDOWN\nMVDOWN")
            self.create_action("Unmute", "MUOFF")

            # Row 4
            self.create_action("Zone2 40", "Z240")
            self.create_action("Zone2 55", "Z255")
            self.create_action("Zone2 70", "Z270")

            # Row 5
            self.create_action("Zone2 Up", "Z2UP\nZ2UP")
            self.create_action("Zone2 Up+", "Z2UP\nZ2UP\nZ2UP\nZ2UP\nZ2UP")
            self.create_action("Zone2 Mute", "Z2MUON")

            # Row 6
            self.create_action("Zone2 Down", "Z2DOWN\nZ2DOWN")
            self.create_action("Zone2 Down-", "Z2DOWN\nZ2DOWN\nZ2DOWN\nZ2DOWN\nZ2DOWN")
            self.create_action("Zone2 Unmute", "Z2MUOFF")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS keyedData(key varchar(50) PRIMARY KEY, data varchar(50))")
        actions = self.cursor.execute("SELECT key, data FROM keyedData").fetchall()
        if len(actions) == 0:
            self.cursor.execute("INSERT INTO keyedData(key, data) VALUES(?, ?)", ("ip", ""))

        self.con.commit()

    def get_ip(self):
        """Get the ip"""
        ip = self.cursor.execute("SELECT data FROM keyedData WHERE key = 'ip'").fetchall()
        return ip[0][0]

    def set_ip(self, ip):
        self.cursor.execute("UPDATE keyedData SET data = ? WHERE key = 'ip'", (ip,))
        self.con.commit()

    def create_action(self, label_text, action_text):
        """Create a action"""
        self.cursor.execute("INSERT INTO actions(label, action) \
                            VALUES(?, ?)", (label_text, action_text))
        self.con.commit()

    def get_actions(self):
        """Get actions"""
        actions = self.cursor.execute("SELECT id, label, action FROM actions").fetchall()
        return actions

    def delete_action(self, action):
        """Delete an action"""
        self.cursor.execute("DELETE FROM actions WHERE action=?", (action,))
        self.con.commit()

    def close_db_connection(self):
        self.con.close()
