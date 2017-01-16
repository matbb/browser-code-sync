Synchronize code between browser and external editor
====================================================

A script to synchronize code loaded in browser with external editor.

This script can pull / push / synchronize the code displayed in a _CodeMirror_ 
code editor used on some of the popular websites used for sharing code or learning how to code 
( [codepen](codepen.io), [freecodecamp](freecodecamp.com), ... ) 
with a file on disk, so you can use your favourite code editor.

I wrote this script when I wanted to learn some javascript from [freecodecamp](freecodecamp.com), 
but had little patience for in-browser code-editors. 
I wanted a setup where I could control when the code gets pulled / pushed to vim 
and also wanted to be able to advance to next challenge/validate code from within vim.

To use the script, you have to : 
  * start the chromium browser with remote debugging enabled 
  * use only one tab in the browser window, where you want to synchronize the code to / from 
which means you will need a dedicated chromium instance and will 
have to use another browser instance for browsing.

As an alternative, you might be interested in the following browser extensions : 
[GhostText](https://github.com/GhostText/GhostText), [It's All Text!](https://github.com/docwhat/itsalltext)

Installation 
------------
Install required python modules :
```bash
$ sudo pip3 install chromote watchdog argparse
```
and clone this git repository.

Example usage 
-------------
Start a dedicated chromium browser window  with remote-debugging protocol 
```bash
$ chromium-browser -remote-debugging-port=9222 --temp-profile
```
If you want to use your main browser session, omit the `--temp-profile` flag.

### Vim with manual code push / pull
Edit the provided [vimrc example](./vimrc) with the proper location of the script and source it with  
```vim
:source /path/to/script/vimrc
```
in vim or add the settings to your _.vimrc_.

The example keybindings provide the following shortcuts, where N is the number of the current buffer :
  * __Ctrl+H__ : pushes the contents of the current buffer to the Nth CodeMirror editor found in browser
  * __Ctrl+L__ : pulls the contents of the Nth CodeMirror editor in the browser into the current buffer
  * __Ctrl+J__ : presses the submit button on freecodecamp
  * __Ctrl+K__ : presses the next-challenge button on freecodecamp

so provided that you launched vim wih :
```bash 
$ vim t1.html t2.css t3.js
```
your buffers would be correctly synced to codepen's code editors.

### Synchronizing to files on disk

Start file sync :
```bash 
$ /path/to/script/browser-code-sync.py syncfolder ~/Desktop ~/Desktop/f1.html ~/Desktop/f2.css ~/Desktop/f3.js
```
will synchronize files _f1.html_, _f2.css_ and _f3.js_ with the contents of the 1st, 2nd and 3rd _CodeMirror_ editor found in your browser window. 
On first run the script will pull the contents from the browser into the files. When files change on disk, the contents will be pushed to the browser.

### Manual code push / pull 
To use the script from another code editor, bind the appropriate keys to the push / pull commands.
For example
```bash 
$ /path/to/script/browser-code-sync.py push filename 2
```
pushes the contents of file _filename_ into the 2nd CodeMirror editor open in the browser, and
```bash 
$ /path/to/script/browser-code-sync.py pull filename 1
```
pulls the contents of the 1st CodeMirror editor open in the browser into the file _filename_.

Screencasts
-----------
Click on the images to enlarge.
Some key presses are missing.

### Freecodecamp 
![Freecodecamp: completing a challenge](./images/freecodecamp.gif)

### Vim: manual mode
![Vim: manual mode](./images/vim-manual-sync.gif)

### Vim: automatic sync 
![Vim: folder sync](./images/vim-folder-sync.gif)


Platforms 
---------
I tested the script on ubuntu xenial/trusty with chromium browser. All above instructions were tested on ubuntu xenial.
To use the script a different os, run the script with your python3 interpreter. 
I think this should not be difficult, but haven't tested it.

Reporting bugs
--------------
Please include the full contents of the file you were trying to synchronize along with os and python version you are using.
