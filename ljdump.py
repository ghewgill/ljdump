#!/usr/bin/python
#
# ljdump.py - livejournal archiver
# Greg Hewgill <greg@hewgill.com> http://hewgill.com
# Version 1.1
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
# to date. Both new and updated items are downloaded.
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
# Copyright (c) 2005-2006 Greg Hewgill

import codecs, md5, os, pickle, pprint, re, sys, urllib2, xml.dom.minidom, xmlrpclib
from xml.sax import saxutils

def calcchallenge(challenge, password):
    return md5.new(challenge+md5.new(password).hexdigest()).hexdigest()

def flatresponse(response):
    r = {}
    while True:
        name = response.readline()
        if len(name) == 0:
            break
        if name[-1] == '\n':
            name = name[:len(name)-1]
        value = response.readline()
        if value[-1] == '\n':
            value = value[:len(value)-1]
        r[name] = value
    return r

def getljsession(username, password):
    r = urllib2.urlopen(Server+"/interface/flat", "mode=getchallenge")
    response = flatresponse(r)
    r.close()
    r = urllib2.urlopen(Server+"/interface/flat", "mode=sessiongenerate&user=%s&auth_method=challenge&auth_challenge=%s&auth_response=%s" % (username, response['challenge'], calcchallenge(response['challenge'], password)))
    response = flatresponse(r)
    r.close()
    return response['ljsession']

def dochallenge(params, password):
    challenge = server.LJ.XMLRPC.getchallenge()
    params.update({
        'auth_method': "challenge",
        'auth_challenge': challenge['challenge'],
        'auth_response': calcchallenge(challenge['challenge'], password)
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

def createxml(doc, name, map):
    e = doc.createElement(name)
    for k in map.keys():
        me = doc.createElement(k)
        me.appendChild(doc.createTextNode(map[k]))
        e.appendChild(me)
    return e

def gettext(e):
    if len(e) == 0:
        return ""
    return e[0].firstChild.nodeValue

config = xml.dom.minidom.parse("ljdump.config")
Server = config.documentElement.getElementsByTagName("server")[0].childNodes[0].data
Username = config.documentElement.getElementsByTagName("username")[0].childNodes[0].data
Password = config.documentElement.getElementsByTagName("password")[0].childNodes[0].data

m = re.search("(.*)/interface/xmlrpc", Server)
if m:
    Server = m.group(1)

print "Fetching journal entries for: %s" % Username
try:
    os.mkdir(Username)
    print "Created subdirectory: %s" % Username
except:
    pass

ljsession = getljsession(Username, Password)

server = xmlrpclib.ServerProxy(Server+"/interface/xmlrpc")

newentries = 0
newcomments = 0
errors = 0

lastsync = ""
lastmaxid = 0
try:
    f = open("%s/.last" % Username, "r")
    lastsync = f.readline()
    if lastsync[-1] == '\n':
        lastsync = lastsync[:len(lastsync)-1]
    lastmaxid = f.readline()
    if len(lastmaxid) > 0 and lastmaxid[-1] == '\n':
        lastmaxid = lastmaxid[:len(lastmaxid)-1]
    if lastmaxid == "":
        lastmaxid = 0
    else:
        lastmaxid = int(lastmaxid)
    f.close()
except:
    pass
origlastsync = lastsync

while True:
    r = server.LJ.XMLRPC.syncitems(dochallenge({
        'username': Username,
        'ver': 1,
        'lastsync': lastsync,
    }, Password))
    #pprint.pprint(r)
    if len(r['syncitems']) == 0:
        break
    for item in r['syncitems']:
        if item['item'][0] == 'L':
            print "Fetching journal entry %s (%s)" % (item['item'], item['action'])
            try:
                e = server.LJ.XMLRPC.getevents(dochallenge({
                    'username': Username,
                    'ver': 1,
                    'selecttype': "one",
                    'itemid': item['item'][2:],
                }, Password))
                writedump("%s/%s" % (Username, item['item']), e['events'][0])
                newentries += 1
            except xmlrpclib.Fault, x:
                print "Error getting item: %s" % item['item']
                pprint.pprint(x)
                errors += 1
        lastsync = item['time']

# The following code doesn't work because the server rejects our repeated calls.
# http://www.livejournal.com/doc/server/ljp.csp.xml-rpc.getevents.html
# contains the statement "You should use the syncitems selecttype in
# conjuntions [sic] with the syncitems protocol mode", but provides
# no other explanation about how these two function calls should
# interact. Therefore we just do the above slow one-at-a-time method.

#while True:
#    r = server.LJ.XMLRPC.getevents(dochallenge({
#        'username': Username,
#        'ver': 1,
#        'selecttype': "syncitems",
#        'lastsync': lastsync,
#    }, Password))
#    pprint.pprint(r)
#    if len(r['events']) == 0:
#        break
#    for item in r['events']:
#        writedump("%s/L-%d" % (Username, item['itemid']), item)
#        newentries += 1
#        lastsync = item['eventtime']

print "Fetching journal comments for: %s" % Username

try:
    f = open("%s/comment.meta" % Username)
    metacache = pickle.load(f)
    f.close()
except:
    metacache = {}

try:
    f = open("%s/user.map" % Username)
    usermap = pickle.load(f)
    f.close()
except:
    usermap = {}

maxid = lastmaxid
while True:
    r = urllib2.urlopen(urllib2.Request(Server+"/export_comments.bml?get=comment_meta&startid=%d" % (maxid+1), headers = {'Cookie': "ljsession="+ljsession}))
    meta = xml.dom.minidom.parse(r)
    r.close()
    for c in meta.getElementsByTagName("comment"):
        id = int(c.getAttribute("id"))
        metacache[id] = {
            'posterid': c.getAttribute("posterid"),
            'state': c.getAttribute("state"),
        }
        if id > maxid:
            maxid = id
    for u in meta.getElementsByTagName("usermap"):
        usermap[u.getAttribute("id")] = u.getAttribute("user")
    if maxid >= int(meta.getElementsByTagName("maxid")[0].firstChild.nodeValue):
        break

f = open("%s/comment.meta" % Username, "w")
pickle.dump(metacache, f)
f.close()

f = open("%s/user.map" % Username, "w")
pickle.dump(usermap, f)
f.close()

newmaxid = maxid
maxid = lastmaxid
while True:
    r = urllib2.urlopen(urllib2.Request(Server+"/export_comments.bml?get=comment_body&startid=%d" % (maxid+1), headers = {'Cookie': "ljsession="+ljsession}))
    meta = xml.dom.minidom.parse(r)
    r.close()
    for c in meta.getElementsByTagName("comment"):
        id = int(c.getAttribute("id"))
        jitemid = c.getAttribute("jitemid")
        comment = {
            'id': str(id),
            'parentid': c.getAttribute("parentid"),
            'subject': gettext(c.getElementsByTagName("subject")),
            'date': gettext(c.getElementsByTagName("date")),
            'body': gettext(c.getElementsByTagName("body")),
            'state': metacache[id]['state'],
        }
        if usermap.has_key(c.getAttribute("posterid")):
            comment["user"] = usermap[c.getAttribute("posterid")]
        try:
            entry = xml.dom.minidom.parse("%s/C-%s" % (Username, jitemid))
        except:
            entry = xml.dom.minidom.getDOMImplementation().createDocument(None, "comments", None)
        found = False
        for d in entry.getElementsByTagName("comment"):
            if int(d.getElementsByTagName("id")[0].firstChild.nodeValue) == id:
                found = True
                break
        if found:
            print "Warning: downloaded duplicate comment id %d in jitemid %s" % (id, jitemid)
        else:
            entry.documentElement.appendChild(createxml(entry, "comment", comment))
            f = codecs.open("%s/C-%s" % (Username, jitemid), "w", "UTF-8")
            entry.writexml(f)
            f.close()
            newcomments += 1
        if id > maxid:
            maxid = id
    if maxid >= newmaxid:
        break

lastmaxid = maxid

f = open("%s/.last" % Username, "w")
f.write("%s\n" % lastsync)
f.write("%s\n" % lastmaxid)
f.close()

if origlastsync:
    print "%d new entries, %d new comments (since %s)" % (newentries, newcomments, origlastsync)
else:
    print "%d new entries, %d new comments" % (newentries, newcomments)
if errors > 0:
    print "%d errors" % errors
