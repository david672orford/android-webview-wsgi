## Purpose

This project can be used to pack a Python WSGI web server into an Android app along
with an Android webview to browser it.

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

