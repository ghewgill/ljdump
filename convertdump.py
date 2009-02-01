#!/usr/bin/python

import xml.dom.minidom 
import os
import codecs
import sys

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
    nodeValue = value

    # make sure value is properly encoded
    try:
        bytes = nodeValue.encode("UTF-8")
    except:
        bytes = nodeValue.encode("cp1252")
        nodeValue = unicode(bytes, "UTF-8")

    element = doc.createElement(nodename)

    if( nodeValue != "" ): 
        textNode = doc.createTextNode(nodeValue)
        element.appendChild(textNode)

    parent.appendChild(element)


def addEntryForId(outDoc, element, username, id):
    entryFile = open("%s/L-%s" % (username,id), "r")
    inDoc = xml.dom.minidom.parse(entryFile)

    # Create an entry element
    entry = outDoc.createElement("entry")
    element.appendChild(entry)

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
    maskText = getNodeText(inDoc, "allowmask")

    # XXXSMG: consult L-1411 and L-976 for examples of security and
    # allowmask use
    if(maskText != ""):
        appendTextNode(outDoc, entry, "allowmask", maskText)
    else:
        appendTextNode(outDoc, entry, "allowmask", "0")

    # Create a taglist element
    appendTextNode(outDoc, entry, "taglist", getNodeText(inDoc, "taglist"))

    # XXXSMG: make sure there is a comment file before trying to do anything
    # with it
    addCommentsForId(outDoc, entry, username, id)

def addCommentsForId(outDoc, entry, username, id):
    try: 
        commentFile = open("%s/C-%s" % (username,id), "r")
    except IOError:  # there are no comments for this entry
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

def main(argv): 
    username = ""
    entryLimit = 250
    

    if( len(argv) != 2 ):
        print( "Usage: convertdump.py <username> <entrylimit>" )
        return
    else:
        username = argv[0]
        entryLimit = int(argv[1])

    userDir = os.listdir(username)

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


    # Create the minidom document
    outDoc = xml.dom.minidom.Document()

    # Create the <livejournal> base element
    ljElement = outDoc.createElement("livejournal")
    outDoc.appendChild(ljElement)

    currentFileEntry = 0

    # start processing entries
    for entry in entryArray:
        addEntryForId(outDoc, ljElement, username, entry)

        currentFileEntry += 1

        if( currentFileEntry == entryLimit or entry == entryArray[-1] ):

            f = open("%s - %s.xml" % (username, entry), "w")
            tempXML = outDoc.toxml("UTF-8")
            f.write(tempXML)
            
            currentFileEntry = 0

            # Create the minidom document
            outDoc = xml.dom.minidom.Document()

            # Create the <livejournal> base element
            ljElement = outDoc.createElement("livejournal")
            outDoc.appendChild(ljElement)

if __name__ == "__main__":
    main(sys.argv[1:])

