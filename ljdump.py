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

def writedump(itemid, event):
    f = codecs.open("archive/"+itemid, "w", "UTF-8")
    f.write("""<?xml version="1.0"?>\n""")
    dumpelement(f, "event", event)
    f.close()

config = xml.dom.minidom.parse("ljdump.config")
Username = config.documentElement.getElementsByTagName("username")[0].childNodes[0].data
Password = config.documentElement.getElementsByTagName("password")[0].childNodes[0].data

server = xmlrpclib.ServerProxy("http://livejournal.com/interface/xmlrpc")
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
        #print item['item']
        if item['item'][0] == 'L':
            if not os.access("archive/"+item['item'], os.F_OK):
                try:
                    e = server.LJ.XMLRPC.getevents(dochallenge({
                        'username': Username,
                        'ver': 1,
                        'selecttype': "one",
                        'itemid': item['item'][2:],
                    }, Password))
                    writedump(item['item'], e['events'][0])
                except xmlrpclib.Fault, x:
                    print "Error getting item: %s" % item['item']
                    pprint.pprint(x)
        last = item['time']
