#! /bin/sh
set -e

if false
	then
	# Build libmain.so
	$HOME/bin-annex/android-ndk-r10e/ndk-build
	
	# Install libpython and libsqlite3
	cp python-install/lib/libpython*.so libs/armeabi/
	#cp python-install/lib/libsqlite3.so libs/armeabi/
	strip libs/armeabi/*.so
	fi

# Assemble the assets and generate app configuration files
#./build.py --wsgi-app=examples/app_basic --modules=wsgiref --package com.example.test --name Test --version 0.1
#./build.py --wsgi-app=examples/app_werkzeug --modules=werkzeug,jinja2 --package com.example.test --name Test --version 0.1
#./build.py --wsgi-app=examples/app_flask --modules=werkzeug,jinja2,flask --package com.example.test --name Test --version 0.1
./build.py --wsgi-app=../Parallel_Reader/app --modules=werkzeug,jinja2,pil,tlslite,etree --package com.example.test --name Test --version 0.1

# Build the apk
./gradlew assembleDebug
ls -l build/outputs/apk/debug/android-webview-wsgi-debug.apk
adb install -r build/outputs/apk/debug/android-webview-wsgi-debug.apk

# Watch for messages from our bootstrap
echo "Logcat..."
adb logcat -c
adb logcat | grep -i python

