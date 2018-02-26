# Bear Notes App Exporter and Sync

This script will export new files from the SQLite database where Bear stores all notes. It assumes that every note has exactly one tag and uses that as the filepath in the exported files.

It will additionally sync files that already exist in the database, taking either the exported or the database version depending on the date they were last modified.

It will NOT import new files into the database -- please use Bear's built-in import function for this. Once the file has been imported it can be synced as normal.

## Installation
This script needs Python to run. I've only tested it on Python 3, but it may work with Python 2 as well.

1. Install Python requirements: `pip3 install -r requirements`.
2. Update the username and sync location in `main.py` to be what you want.
3. Update the path to `main.py` in the `.plist` file. By default, it is assumed that this is `~/Applications/bear-sync/main.py`.
4. Copy the `.plist` to the correct location: `cp com.gautampk.bear-sync.plist ~/Libaray/LaunchAgents/`.
5. Either logout and login to start the service, or run `launchctl start com.gautampk.bear-sync`.

## Licence
Copyright 2018 gautampk, licensed under the MIT licence.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
