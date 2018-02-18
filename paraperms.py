"""
    Defines the permission functions which act as gates to check whether users have certain permissions.
"""

import asyncio

# Define permission dictionary
permFuncs = {}


def perm_func(permName):
    def decorator(func):
        permFuncs[permName.lower()] = [func]
        return func
    return decorator


# ------PERMISSION FUNCTIONS------

@perm_func("Master")
async def perm_master(client, botdata, conf=None, message=None, user=None, server=None):
    if message is not None:
        user = message.author
    if user is not None:
        userid = user.id
    if (user is None) or (conf is None):
        return(2, "Something went wrong inside me!")
    if int(userid) not in conf.getintlist("masters"):
        msg = "This requires you to be one of my masters!"
        return (1, msg)
    return (0, "")


@perm_func("Exec")
async def perm_exec(client, botdata, conf=None, message=None, user=None, server=None):
    if message is not None:
        user = message.author
        server = message.server
    if user is not None:
        userid = user.id
    if (user is None) or (conf is None):
        return(2, "An internal error occurred.")

    (mastererror, msg) = await permFuncs["master"][0](client, botdata, conf, message, user, server)
    if mastererror == 0:
        return (mastererror, msg)
    if int(userid) not in conf.getintlist("execWhiteList"):
        msg = "You don't have the required Exec perms to do this!"
        return (1, msg)
    return (0, "")


@perm_func("Manager")
async def perm_manager(client, botdata, conf=None, message=None, user=None, server=None):
    if message is not None:
        user = message.author
        server = message.server
    if user is not None:
        userid = user.id
    if (user is None) or (conf is None):
        return(2, "An internal error occurred.")

    (execerror, msg) = await permFuncs["exec"][0](client, botdata, conf, message, user, server)
    if execerror == 0:
        return (execerror, msg)
    if int(userid) not in conf.getintlist("managers"):
        msg = "You lack the required bot manager perms to do this!"
        return (1, msg)
    return (0, "")

"""
TODO: check whether server_permissions accounts for server owner
"""

@perm_func("in server")
async def perm_in_server(client, botdata, conf=None, message=None, user=None, server=None):
    if (message is None):
        return(2, "An internal error occurred.")
    if not message.server:
        return(1, "This can only be used in a server!")
    return(0, "")

@perm_func("manage_server")
async def perm_manage_server(client, botdata, conf=None, message=None, user=None, server=None):
    if message is not None:
        user = message.author
        server = message.server
    if (user is None) or (server is None):
        return (2, "An internal error occurred.")
    if not (user.server_permissions.manage_server or user.server_permissions.administrator):
        return (1, "You lack the `Manage Server` permission on this server!")
    return (0, "")
# ----End permission functions----
