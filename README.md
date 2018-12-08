## Purpose

This project can be used to pack a Python WSGI web server into an Android app along
with an Android webview to browser it. It is an improved version of an Android
project produced with Python for Android with the "webview" bootstrap.

The Android packages produced by Python for Android (as of version 0.6) pack all
of the Python code into a large tar file which is unpacked into the applications
file space when it is first run. This slows down the first start and wastes about
15MB of space. Apps packages by this project run directly from the apk file using
the zipimport module to load code and the zipfile module to load (read-only) data
files.

This project addresses an unsolved problem in the Python for Android webview
bootstrap. This is that the webview must be connected to the web server running
in the Python thread, but at the time the webview opens the server probably is
not started yet and its port number is unknown. Currently this is handled by
having the person running the packaging process pick a port number which hopefully
will be free. A special thread is started which repeatedly tries to connect to the
server until it appears. When the server appears, the webview is instructed to
connect to it. Until then, it displays a "loading" page.

In this project we solve the problem by having the web server accept whatever
free port the operating system assigns it (by not calling bind()). Once the
listening port has been created, the Python bootstrap code calls back into the
Java code to command the webview to navigate to the URL of the web server.

The bootstrap code is able to do this because it does not run a main.py script
as the "webview" bootstrap does. Instead it imports a WSGI application supplied
by the user and dispatches requests to it. (Which means that it runs them
as a web server with WSGI support would.) This allows the bootstrap code to
properly control the start up process.

## The Bootstrap Process

1. PythonActivity creates a webview and points it at assets/bootstrap.html
   where it sits waiting.
2. PythonActivity calls a native function in start.c which gets and saves
   a reference to loadUrl in the Java bootstrap.
3. PythonActivity then sets environment variables begining with "ANDROID\_".
   These tell the other parts of the bootstrap where to find things and what
   the apps name is.
4. PythonActivity then create a thread and runs the native code in it.
5. Start.c does a chdir() to the application's FilesDir
6. Start.c code creates a Python interpreter
7. Start.c creates a module called "android" in the interpreter with
   a method log() to write to the Android log and loadUrl() to change
   the address of the webview (by using the reference to the Java code saved
   earlier.
8. Start.c uses runpy to run bootstrap.py which is zipped inside
   the apk.
9. Boostrap.py creates a writable file-like object which invokes android.log()
   and replaces sys.stdout and sys.stderr with an instance of it.
10. Bootstrap.py opens the apps apk file using zipfile from the standard
   Python library and hooks open() and os.stat() so that they can operate
   on files which are inside it.
10. Bootstrap.py imports the user's WSGI application from the assets directory.
11. Bootstrap.py wraps the WSGI app so that it will only accept requests from
   the Android webview in this Android app.
12. Bootstrap.py loads werkzeug (or failing that wsgiref) and creates a listening
   TCP socket on a port assigned by the system.
13. Bootstrap.py constructs a localhost URL using that port and uses
   android.loadURL() to command the webview to navigate to it.
14. Bootstrap.py calls serve\_forever() to answer requests from the webview
  which may have alreaady connected.

## Building an APK

Building an APK from this project currently requires three steps:

1. Configure the project using build.py
 * Has no --port option since the system now picks the port at app startup.
 * Has no --private option since the code to unpack a tar file into
   FilesDir has been stripped out.
 * Has a --wsgi-app option. Use --wsgi-app=examples/app\_basic for
   a raw WSGI hello world app.
 * Has --modules to select which Python library modules to include.
   Currently the following are your options:
   * --modules=wsgiref
   * --modules=werkzeug
   * --modules=werkzeug,jinja2
   * --modules=werkzeug,jinja2,flask
2. Build the C bootstrap by running ndk-build
3. Copy libpython and any additional libraries into libs/armeabi and strip them
4. Build the APK using Gradle by running gradlew

The script install.sh is a sample which shows how to perform the above steps
to pack the sample apps.

## Project Layout

* jni -- the C part of the bootstrap, ndk-build builds it
 * obj -- where the intermediate files built from jni/ go
 * libs -- where the final files build from jni/ go

* src -- the Java part of the bootstrap

* python-install -- libpython and all of the python modules

* assets/python -- build.py copies selected modules from python-install to here

* assets/app -- build.py copies the files indicated by --wsgi-app to here

* assets/bootstrap\* -- startup code

* examples -- example WSGI applications using various frameworks

## Changes From the Webview Bootstrap in P4A 0.6

This project was produce by modifying one built by Python For Android.
Here is a summary of the changes:

* jni/src/Android.mk
  * Corrected paths to python-install
  * Link in libpython2.7.
* jni/src/start.c
  * Removed service support for now
  * Moved the Python bootstrap code into assets/bootstrap.py
  * Renamed the "androidembed" package to "android"
  * Added android.loadUrl
* src/
  * Following features removed for now:
    * some kind of support for in-app purchases
      * support for running a second Python interpreter as a service
      * support for wakelock
  * Added android.loadUrl
    * Dropped unfinished code in \_load.html which waits for the WSGI app to start
    * Dropped pinger which did the same thing (it worked, but with android.loadUrl it is unnecessary)
  * Pause JavaScript timers when app in background
  * Fixed location.replace() from JavaScript
  * Dropped the use of a layout since we have only one widget
  * Dropped numerous unnecessary imports
* assets/bootstrap.py
    * The Python bootstrap code has been moved from start.c to here
    * Now overrides open() and os.stat() so that apps can run out of the apk
    * The server port is no longer hard-coded
    * Other apps on the same device can no longer use the server
  * Rather than running main.py, it imports app.app and runs it as a WSGI app
* build.py
    * removed --private option since this tar unpacking code has been removed
    * removed --port option	since our bootstrap selects it automatically
  * removed --whitelist and --blacklist options in favor of --modules
  * removed --wakelock option (not supported in our stripped-down bootstrap)
    * removed --add-source option (not supported in our Gradle file)
  * removed --permission
  * removed --meta-data
  * added --wsgi-app option
  * added --modules option
* The Ant build.xml file has been replaced with Gradle and build.gradle.

## Site Modules

When Python for Android was used to create the project on which this one is based
the following additional modules were selected:

* flask
* werkzeug
* sqlite3

The following Python modules have been manuall added
to python-install/lib/python2.7/site-packages/:

* tlslite-ng (with loading of verifierdb commented out in api.py)
* ecdsa (on which tlslite-ng depends)
* six (on which tlslite-ng also depends)

