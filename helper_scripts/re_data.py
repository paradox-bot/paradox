import sqlite3 as sq

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


old_file = "botdata.db"

old_conn = sq.connect(old_file)
old_conn.row_factory = dict_factory


server_data = {}
sql = "SELECT * FROM servers "
cursor = old_conn.execute(sql)
for row in cursor.fetchall():
    serverid = row.pop("serverid")
    print("Adding row for server {}".format(serverid))
    server_data[serverid] = row

user_data = {}
sql = "SELECT * FROM users "
cursor = old_conn.execute(sql)
for row in cursor.fetchall():
    userid = row.pop("userid")
    print("Adding row for user {}".format(userid))
    user_data[userid] = row


new_file = "paradata.db"
new_conn = sq.connect(new_file)
cursor = new_conn.cursor()

# Schema
cursor.execute('CREATE TABLE servers ( serverid INTEGER NOT NULL,\
               property TEXT NOT NULL,\
               value TEXT,\
               PRIMARY KEY (serverid, property))')
cursor.execute('CREATE TABLE users ( userid INTEGER NOT NULL,\
               property TEXT NOT NULL,\
               value TEXT,\
               PRIMARY KEY (userid, property))')
cursor.execute('CREATE TABLE members ( serverid INTEGER NOT NULL,\
               userid INTEGER NOT NULL,\
               property TEXT NOT NULL,\
               value TEXT,\
               PRIMARY KEY (serverid, userid, property))')
cursor.execute('CREATE TABLE users_props ( property TEXT NOT NULL,\
               shared BOOLEAN NOT NULL,\
               PRIMARY KEY (property))')
cursor.execute('CREATE TABLE servers_props ( property TEXT NOT NULL,\
               shared BOOLEAN NOT NULL,\
               PRIMARY KEY (property))')
cursor.execute('CREATE TABLE members_props ( property TEXT NOT NULL,\
               shared BOOLEAN NOT NULL,\
               PRIMARY KEY (property))')

# Transfer server data
for server in server_data:
    for prop in server_data[server]:
        value = server_data[server][prop]
        if value is None:
            continue
        cursor.execute('INSERT INTO servers VALUES (?, ?, ?)', (server, prop, value))
new_conn.commit()

# Transfer user data
for user in user_data:
    for prop in user_data[user]:
        value = user_data[user][prop]
        if value is None:
            continue
        cursor.execute('INSERT INTO users VALUES (?, ?, ?)', (user , prop, value))
new_conn.commit()
