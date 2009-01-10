#!/usr/bin/python
#
# ljdump-gui.py - gui interface to ljdump
# Greg Hewgill <greg@hewgill.com> http://hewgill.com
#
# NOTE: This is a work in progress and is probably not suitable for
#       general release just yet.
#
# LICENSE
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the author be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
#
# Copyright (c) 2005-2009 Greg Hewgill

import sys
import threading

from Tkinter import *

import ljdump

gWorkerThread = None

def poll():
    global gWorkerThread
    if gWorkerThread.isAlive():
        root.after(100, poll)
    else:
        gWorkerThread = None
        status['text'] = "Completed."
        ok['state'] = NORMAL
        cancel['state'] = NORMAL

def do_ok(event = None):
    print "ok"
    #root.withdraw()
    status['text'] = "Running..."
    ok['state'] = DISABLED
    cancel['state'] = DISABLED
    global gWorkerThread
    gWorkerThread = threading.Thread(None, ljdump.ljdump, args=("http://livejournal.com", username.get(), password.get()))
    gWorkerThread.start()
    poll()

def do_cancel(event = None):
    print "cancel", event
    root.destroy()

root = Tk()
root.title("ljdump")

body = Frame(root)
Label(body, text="Username:").grid(row=0, sticky=W)
Label(body, text="Password:").grid(row=1, sticky=W)
Label(body, text="Status:").grid(row=2, sticky=W)
username = Entry(body)
password = Entry(body, show="*")
status = Label(body, text="Waiting")
username.grid(row=0, column=1)
password.grid(row=1, column=1)
status.grid(row=2, column=1, sticky=W)
body.pack(padx=5, pady=5)

box = Frame(root)

ok = Button(box, text="OK", width=10, command=do_ok, default=ACTIVE)
ok.pack(side=LEFT, padx=5, pady=5)
cancel = Button(box, text="Cancel", width=10, command=do_cancel)
cancel.pack(side=LEFT, padx=5, pady=5)

root.bind("<Return>", do_ok)
root.bind("<Escape>", do_cancel)

box.pack()

username.focus_set()
root.mainloop()
