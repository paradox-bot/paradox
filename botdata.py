'''
    BotData class, supersceding the old UserConf class.
    Still a basic implementation using INF files and JSON.
    TODO: Update to using a database (tinysql etc), but keep approximately the same interface.
'''
import sqlite3 as sq
import json

class BotData:
    userTable = 'Users'
    serverTable = 'Servers'
    def __init__(self, dbfile):
        self.conn = sq.connect(dbfile)
        cursor = self.conn.cursor()
        try:
            cursor.execute('CREATE TABLE {} (userid INTEGER PRIMARY KEY)'.format(self.userTable))
        except Exception:
            pass
        try:
            cursor.execute('CREATE TABLE {} (serverid INTEGER PRIMARY KEY)'.format(self.serverTable))
        except Exception:
            pass
        self.users = _dbDataManipulator(self.userTable, "userid", self.conn)
        self.servers = _dbDataManipulator(self.serverTable, "serverid", self.conn)
    def close(self):
        self.conn.commit()
        self.conn.close()


class _dbDataManipulator:
    def __init__(self, table, keyname, connection):
        self.table = table
        self.keyname = keyname
        self.conn = connection

    def get(self, key, prop, default = None):
        curs = self.conn.cursor()
        try:
            curs.execute('ALTER TABLE {} ADD {} text'.format(self.table, prop))
        except Exception:
            pass
        curs.execute('SELECT {} FROM {} WHERE {} = ?'.format(prop, self.table, self.keyname), (key,))
        value = curs.fetchone()
        return json.loads(value[0]) if (value and value[0]) else default
    def set(self, key, prop, value):
        cursor = self.conn.cursor()
        try:
            cursor.execute('ALTER TABLE {} ADD {} text'.format(self.table, prop))
        except Exception:
            pass
        cursor.execute('SELECT EXISTS(SELECT 1 FROM {} WHERE {} = ?)'.format(self.table, self.keyname), (key,))
        exists = cursor.fetchone()
        if not exists[0]:
            cursor.execute('INSERT INTO {} ({}) VALUES (?)'.format(self.table, self.keyname), (key,))

        cursor.execute('UPDATE {} SET {} = ? WHERE {} = ?'.format(self.table, prop, self.keyname), (json.dumps(value), key))
        self.conn.commit()
    def find(self, prop, value, read=False):
        if read:
            value = json.dumps(value)
        curs = self.conn.cursor()
        curs.execute('SELECT {} FROM {} WHERE {} = ?'.format(self.keyname, self.table, self.prop), (value,))
        values = curs.fetchall()
        return [json.loads(value) for value in values]
