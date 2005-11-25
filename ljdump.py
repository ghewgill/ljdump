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
Username = config.documentElement.getElementsByTagName("username")[0].childNodes[0].data
Password = config.documentElement.getElementsByTagName("password")[0].childNodes[0].data

print "Fetching journal entries for: %s" % Username
try:
    os.mkdir(Username)
    print "Created subdirectory: %s" % Username
except:
    pass

server = xmlrpclib.ServerProxy("http://livejournal.com/interface/xmlrpc")

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
        last = item['time']
        total += 1
print "%d total entries" % total
print "%d fetched entries" % fetched
if errors > 0:
    print "%d errors" % errors
