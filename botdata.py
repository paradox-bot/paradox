'''
    Class which stores all required botdata in an sqllite database
'''
import json
import sqlite3 as sq


class BotData:
    userTable = 'Users'
    serverTable = 'Servers'

    def __init__(self, dbfile):
        self.conn = sq.connect(dbfile)
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'CREATE TABLE {} (userid INTEGER PRIMARY KEY)'.format(
                    self.userTable))
        except Exception:
            pass
        try:
            cursor.execute(
                'CREATE TABLE {} (serverid INTEGER PRIMARY KEY)'.format(
                    self.serverTable))
        except Exception:
            pass
        self.users = _dbDataManipulator(self.userTable, "userid", self.conn)
        self.servers = _dbDataManipulator(self.serverTable, "serverid",
                                          self.conn)

    def close(self):
        self.conn.commit()
        self.conn.close()


class _dbDataManipulator:
    def __init__(self, table, keyname, connection):
        self.table = table
        self.keyname = keyname
        self.conn = connection

    async def get(self, key, prop, default=None):
        curs = self.conn.cursor()
        try:
            curs.execute('ALTER TABLE {} ADD {} text'.format(self.table, prop))
        except Exception:
            pass
        curs.execute(
            'SELECT {} FROM {} WHERE {} = ?'.format(prop, self.table,
                                                    self.keyname), (key, ))
        value = curs.fetchone()
        return json.loads(value[0]) if (value and value[0]) else default

    async def set(self, key, prop, value):
        cursor = self.conn.cursor()
        try:
            cursor.execute('ALTER TABLE {} ADD {} text'.format(
                self.table, prop))
        except Exception:
            pass
        cursor.execute(
            'SELECT EXISTS(SELECT 1 FROM {} WHERE {} = ?)'.format(
                self.table, self.keyname), (key, ))
        exists = cursor.fetchone()
        if not exists[0]:
            cursor.execute(
                'INSERT INTO {} ({}) VALUES (?)'.format(
                    self.table, self.keyname), (key, ))

        cursor.execute(
            'UPDATE {} SET {} = ? WHERE {} = ?'.format(
                self.table, prop, self.keyname), (json.dumps(value), key))
        self.conn.commit()

    async def find(self, prop, value, read=False):
        if read:
            value = json.dumps(value)
        curs = self.conn.cursor()
        try:
            curs.execute('ALTER TABLE {} ADD {} text'.format(self.table, prop))
        except Exception:
            pass
        curs.execute(
            'SELECT {} FROM {} WHERE {} = ?'.format(self.keyname, self.table,
                                                    prop), (value, ))
        values = curs.fetchall()
        return [value[0] for value in values]

    async def find_not_empty(self, prop):
        curs = self.conn.cursor()
        await self.ensure_exists(prop)
        curs.execute(
            'SELECT {key} FROM {table} WHERE {prop} IS NOT NULL AND {prop} != \'\''
            .format(key=self.keyname, table=self.table, prop=prop))
        values = curs.fetchall()
        return [value[0] for value in values]

    async def ensure_exists(self, prop):
        curs = self.conn.cursor()
        try:
            curs.execute('ALTER TABLE {} ADD {} text'.format(self.table, prop))
        except Exception:
            pass
