ljdump - livejournal archiver

This program reads the journal entries from a livejournal (or compatible)
blog site and archives them in a subdirectory named after the journal name.

The configuration is read from "ljdump.config". A sample configuration is
provided in "ljdump.config.sample", which should be copied and then edited.
The configuration settings are:

  server - The XMLRPC server URL. This should only need to be changed
           if you are dumping a journal that is livejournal-compatible
           but is not livejournal itself.

  username - The livejournal user name. A subdirectory will be created
             with this same name to store the journal entries.

  password - The account password. This password is never sent in the
             clear; the livejournal "challenge" password mechanism is used.

This program may be run as often as needed to bring the backup copy up
to date. Both new and updated items are downloaded.

The community http://ljdump.livejournal.com has been set up for questions
or comments.
