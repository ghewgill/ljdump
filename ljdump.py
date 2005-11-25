#!/usr/bin/python
#
# ljdump.py - livejournal archiver
# Greg Hewgill <greg@hewgill.com> http://hewgill.com
# Version 1.0.1
#
# $Id$
#
# This program reads the journal entries from a livejournal (or compatible)
# blog site and archives them in a subdirectory named after the journal name.
#
# The configuration is read from "ljdump.config". A sample configuration is
# provided in "ljdump.config.sample", which should be copied and then edited.
# The configuration settings are:
#
#   server - The XMLRPC server URL. This should only need to be changed
#            if you are dumping a journal that is livejournal-compatible
#            but is not livejournal itself.
#
#   username - The livejournal user name. A subdirectory will be created
#              with this same name to store the journal entries.
#
#   password - The account password. This password is never sent in the
#              clear; the livejournal "challenge" password mechanism is used.
#
# This program may be run as often as needed to bring the backup copy up
# to date. Only new items are downloaded.
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
# Copyright (c) 2005 Greg Hewgill

import codecs, md5, os, pprint, sys, xml.dom.minidom, xmlrpclib
from xml.sax import saxutils

def dochallenge(params, password):
    challenge = server.LJ.XMLRPC.getchallenge()
    params.update({
        'auth_method': "challenge",
        'auth_challenge': challenge['challenge'],
        'auth_response': md5.new(challenge['challenge']+md5.new(password).hexdigest()).hexdigest()
    })
    return params

def dumpelement(f, name, e):
    f.write("<%s>\n" % name)
    for k in e.keys():
        if isinstance(e[k], {}.__class__):
            dumpelement(f, k, e[k])
        else:
            s = unicode(str(e[k]), "UTF-8")
            f.write("<%s>%s</%s>\n" % (k, saxutils.escape(s), k))
    f.write("</%s>\n" % name)

def writedump(fn, event):
    f = codecs.open(fn, "w", "UTF-8")
    f.write("""<?xml version="1.0"?>\n""")
    dumpelement(f, "event", event)
    f.close()

config = xml.dom.minidom.parse("ljdump.config")
Server = config.documentElement.getElementsByTagName("server")[0].childNodes[0].data
Username = config.documentElement.getElementsByTagName("username")[0].childNodes[0].data
Password = config.documentElement.getElementsByTagName("password")[0].childNodes[0].data

print "Fetching journal entries for: %s" % Username
try:
    os.mkdir(Username)
    print "Created subdirectory: %s" % Username
except:
    pass

server = xmlrpclib.ServerProxy(Server)

total = 0
fetched = 0
errors = 0

last = ""
while True:
    r = server.LJ.XMLRPC.syncitems(dochallenge({
        'username': Username,
        'ver': 1,
        'lastsync': last,
    }, Password))
    #pprint.pprint(r)
    if len(r['syncitems']) == 0:
        break
    for item in r['syncitems']:
        if item['item'][0] == 'L':
            fn = "%s/%s" % (Username, item['item'])
            if not os.access(fn, os.F_OK):
                print "Fetching journal entry %s" % item['item']
                try:
                    e = server.LJ.XMLRPC.getevents(dochallenge({
                        'username': Username,
                        'ver': 1,
                        'selecttype': "one",
                        'itemid': item['item'][2:],
                    }, Password))
                    writedump(fn, e['events'][0])
                    fetched += 1
                except xmlrpclib.Fault, x:
                    print "Error getting item: %s" % item['item']
                    pprint.pprint(x)
                    errors += 1
            total += 1
        last = item['time']
print "%d total entries" % total
print "%d fetched entries" % fetched
if errors > 0:
    print "%d errors" % errors
