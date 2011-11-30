#!/usr/bin/env python

"""
IRC color codes,
as well as bolding.

TODO:
    underline / italics
"""

COLORS = {'white': '\0030', 'black': '\0031',
          'dblue': '\0032', 'dgreen': '\0033',
          'orange': '\0034', 'red': '\0035',
          'purple': '\0036', 'dyellow': '\0037',
          'yellow': '\0038', 'green': '\0039',
          'lblue1': '\00310', 'lblue2': '\00311',
          'blue': '\00312', 'pink': '\00313',
          'grey': '\00314', 'lgrey': '\00315'}

def toColor(s, color):
    "returns irc color code for color + string"
    
    if isColor(color):
        return (COLORS[color] + s + "\003")
    else:
        return ""

def toBold(s):
    "returns bolded string"

    return "\002" + s + "\002"

def toBlink(s):
    return "\006" + s + "\003"

def isColor(s):
    "Is it a color(name)?"

    if not s in COLORS.keys():
        return False
    return True 

