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
free port the operating system assigns it (i.e., by not calling bind().) Once the
listening port has been created, the Python bootstrap code calls back into the
Java code to command the webview to navigate to the URL of the web server.

The bootstrap code in this project does not run a main.py script as the
"webview" bootstrap does. Instead it imports a WSGI application supplied
by the user and dispatches requests to it. (Which means that it runs them
as a web server with WSGI support would.)

## Building an APK

Building an APK requires three steps:

1. Configure the project using build.py
2. Build the C bootstrap using ndk-build
3. Build the APK using Gradle

The script install.sh contains samples of the commands for doing this.

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

This project was produce by modifying one built by Python For Android. Here is a summary
of the changes:

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

## Modules Added

The following Python modules have been added to python-install/lib/python2.7/site-packages/:

* tlslite-ng (with loading of verifierdb commented out in api.py)
* ecdsa (on which tlslite-ng depends)
* six (on which tlslite-ng also depends)

