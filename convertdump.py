#!/usr/bin/python

import xml.dom.minidom 

def getNodeText(doc, nodename):
    rc = ""

    nodelist = doc.getElementsByTagName(nodename)[0].childNodes

    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data

    return rc

def appendTextNode(doc, parent, nodename, value):
    element = doc.createElement(nodename)
    textNode = doc.createTextNode(value)
    element.appendChild(textNode)
    parent.appendChild(element)


def addEntryForID(doc, username, id):
    entryFile = open("%s/L-%s" % (username,id), "r")
    inDoc = xml.dom.minidom.parse(entryFile)

    # Create an entry element
    entry = outDoc.createElement("entry")
    ljElement.appendChild(entry)

    # Create an itemid element
    appendTextNode(outDoc, entry, "itemid", getNodeText(inDoc,"itemid"))

    # Create an eventtime element
    appendTextNode(outDoc, entry, "eventtime", getNodeText(inDoc, "eventtime"))

    # Create an subject element
    appendTextNode(outDoc, entry, "subject", getNodeText(inDoc, "subject"))

    # Create an event node (special case because for some reason there are two
    # 'event' elements in the pydump output, which is probably LJ's fault)
    event = inDoc.getElementsByTagName("event")[0]
    appendTextNode(outDoc, entry, "event", getNodeText(event, "event"))

    # Create an allowmask element (doesn't exist in pydump output if public)
    try:
        appendTextNode(outDoc, entry, "allowmask", 
            getNodeText(inDoc, "allowmask"))
    except:
        appendTextNode(outDoc, entry, "allowmask", "0")

    # Create a taglist element
    appendTextNode(outDoc, entry, "taglist", getNodeText(inDoc, "taglist"))

    # XXXSMG: make sure there is a comment file before trying to do anything
    # with it
    commentFile = open("%s/C-%s" % (username,id), "r")
    

# Create the minidom document
outDoc = xml.dom.minidom.Document()

# Create the <livejournal> base element
ljElement = outDoc.createElement("livejournal")
outDoc.appendChild(ljElement)

addEntryForID(outDoc, "grahams", "2583")

# Print our newly created XML
print outDoc.toprettyxml(indent="  ")
