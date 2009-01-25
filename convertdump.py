#!/usr/bin/python

import xml.dom.minidom 
import os
from time import strptime, strftime

def getNodeText(doc, nodename):
    rc = ""

    try:
        nodelist = doc.getElementsByTagName(nodename)[0].childNodes
    except:
        return ""

    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data

    return rc

def appendTextNode(doc, parent, nodename, value):
    element = doc.createElement(nodename)

    if( value != "" ): 
        textNode = doc.createTextNode(value)
        element.appendChild(textNode)

    parent.appendChild(element)


def addEntryForId(outDoc, username, id):
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
    addCommentsForId(outDoc, entry, username, id)

def addCommentsForId(outDoc, entry, username, id):
    try: 
        commentFile = open("%s/C-%s" % (username,id), "r")
    except:
        # there are no comments for this entry
        return

    inDoc = xml.dom.minidom.parse(commentFile)

    comments = inDoc.getElementsByTagName("comment")

    for comment in comments:
        outComment = outDoc.createElement("comment")
        entry.appendChild(outComment)

        # add the item id for the comment
        appendTextNode(outDoc, outComment, "itemid", 
            getNodeText(comment, "id"))

        # convert the time string
        timeString = getNodeText(comment, "date")
        if( timeString != "" ):
            inDate = strptime(timeString, "%Y-%m-%dT%H:%M:%SZ")
            outDate = strftime("%Y-%m-%d %H:%M:%S", inDate)
            appendTextNode(outDoc, outComment, "eventtime", outDate)
        else:
            emptyTime = outDoc.createElement("eventtime")
            outComment.appendChild(emptyTime)

        # Create an subject element
        appendTextNode(outDoc, outComment, "subject", 
            getNodeText(comment, "subject"))

        # Create an event element
        appendTextNode(outDoc, outComment, "event", 
            getNodeText(comment, "body"))

        # Create the author element
        author = outDoc.createElement("author")
        outComment.appendChild(author)

        try:
            cUser = getNodeText(comment, "user")
        except:
            cUser = "anonymous"

        appendTextNode(outDoc, author, "name", cUser)
        appendTextNode(outDoc, author, "email", cUser + "@livejournal.com")
        
        # Create the parent_itemid
        parentId = getNodeText(comment, "parentid")
        if(parentId != ""): 
            appendTextNode(outDoc, outComment, "parent_itemid", parentId)




# Create the minidom document
outDoc = xml.dom.minidom.Document()

# Create the <livejournal> base element
ljElement = outDoc.createElement("livejournal")
outDoc.appendChild(ljElement)

userDir = os.listdir("grahams")

highNum = -1
entryArray = []

# get the list of entries
for file in userDir:
    if file.startswith("L-"):
        entryNum = int(file.replace("L-",""))

        entryArray.append(entryNum)

        if( highNum < entryNum ):
            highNum = entryNum

entryArray.sort()

# start processing entries
for entry in entryArray:
    print entry
    addEntryForId(outDoc, "grahams", entry)


# Print our newly created XML
print outDoc.toprettyxml(indent="  ")
