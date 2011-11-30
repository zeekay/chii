#!/usr/bin/env python

import yaml
import chii
"""
Install script for chii.
decided not to force people to enter data,
if they don't they can suffer, &^ edit the config.

TODO:
    figure out better grouping, but keep it modular
"""

def getChannels():
    "return a list of channels"

    prompt = "Enter your channels [ #foo,#bar,#purple ]  : "
    chans = raw_input(prompt)
    return [c.strip().strip('#') for c in chans.split(',')]

def getIrcInfo():
    "get nick, name, server, etc"

    nick = raw_input("Bot Nickname: ")
    name = raw_input("Real name: ")
    server = raw_input("Server: ")
    # enter try/except here
    port = input("Port: ")

def getAdmin():
    "get admin(s) for chii"

    prompt = "Enter your admin(s) [nick@host,nick2@host2,...]: "
    admin = raw_input(prompt)
    return [a.strip() for a in admin.split(',')]

def main():
    pass

if __name__ == "__main__":
    pass
