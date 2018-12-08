# Run the WSGI app in assets/app.

import sys

import android
android.log('Android logger is working.')

# Redirect stdout and stderr to the Android log
class LogFile(object):
    def __init__(self):
        self.buffer = ''
    def write(self, s):
        s = self.buffer + s
        lines = s.split("\n")
        for l in lines[:-1]:
            android.log(l)
        self.buffer = lines[-1]
    def flush(self):
        return
sys.stdout = sys.stderr = LogFile()
print "Print output successfully redirected to Android log!"

# Dump the environment variables which show us where the Android directories are.
import os
for name, value in os.environ.items():
    if name.startswith("ANDROID_"):
        print "%s=%s" % (name, value)
apkdir = os.environ['ANDROID_APKDIR']

# Cut down the sys.path
print "sys.path=" + str(sys.path)
assetsdir = apkdir + "/assets"
sys.path = [
    assetsdir,
    assetsdir + "/python/lib/python2.7",
    assetsdir + "/python/lib/python2.7/site-packages",
    assetsdir + "/python/lib/python2.7/lib-dynload/",
    ]
print "Shortened sys.path=" + str(sys.path)

print "Monkey file functions to read from apk..."
import zipfile        # imports io
import stat
import __builtin__
import errno

apk = zipfile.ZipFile(apkdir)
apkdir_root = apkdir + "/"

apk_dirs = set()
for entry in apk.namelist():
    apk_dirs.add(os.path.dirname(entry))    

real_open = __builtin__.open
def apk_open(path, mode="r", *args, **kwargs):
    #print "apk_open(\"%s\",\"%s\")" % (path, mode)
    if path.startswith(apkdir_root):
        member_path = os.path.normpath(path[len(apkdir_root):])
        #print "APK member path:", member_path
        try:
            return apk.open(member_path)
        except KeyError:
            print "apk_open(): not found:", member_path
            raise IOError(errno.ENOENT, "No such file or directory", path)
    return real_open(path, mode, *args, **kwargs)
__builtin__.open = apk_open

real_stat = os.stat
def apk_stat(path):
    #print "apk_stat(\"%s\")" % path
    if path.startswith(apkdir_root):
        member_path = os.path.normpath(path[len(apkdir_root):])
        #print "APK member path:", member_path

        if member_path in apk_dirs:
            return os.stat_result((stat.S_IFDIR | 0755, 0, 0, 1, 0, 0, 0, 0, 0, 0))

        try:
            fi = apk.getinfo(member_path)
        except KeyError:
            print "apk_stat(): not found:", member_path
            raise IOError(errno.ENOENT, "No such file or directory", path)

        statbuf = os.stat_result((
            stat.S_IFREG | 0644,        # st_mode
            0,                            # st_ino
            0,                            # st_dev
            1,                            # st_nlink
            0,                            # st_uid
            0,                            # st_gid
            fi.file_size,                # st_size
            0,                            # st_atime
            0,                            # st_mtime
            0                            # st_ctime
            ))
        #print "statbuf:", statbuf
        return statbuf

    return real_stat(path)
os.stat = apk_stat

# This suppresses futile search for /etc/mimetypes, etc.
try:
    import mimetypes
    mimetypes.init([])
except ImportError:
    pass

print "Loading the WSGI app..."
import traceback
try:
    from app import app
except Exception:
    print "=============================================================="
    traceback.print_exc()
    print "=============================================================="
    sys.exit(1)

# Put a wrapper around the request to reject requests from
# other apps running on the same device.
package_name = os.environ['ANDROID_PACKAGE_NAME']
def app_wrapper(environ, start_response):
    if environ.get('HTTP_X_REQUESTED_WITH') != package_name:
        start_response("403 Forbidden", [])
        return [""]
    else:
        return app(environ, start_response)

print "Creating the WSGI server..."
try:
    from werkzeug.serving import make_server
    server = make_server(host="127.0.0.1", port=0, app=app_wrapper, passthrough_errors=True)
except ImportError:
    from wsgiref.simple_server import make_server
    server = make_server(host="127.0.0.1", port=0, app=app_wrapper)

print "Sending webview to the app..."
android.load_url("javascript:location.replace('http://127.0.0.1:{port}')".format(port=server.socket.getsockname()[1]))

print "Starting the WSGI server..."
try:
    server.serve_forever()
except Exception:
    print "=============================================================="
    traceback.print_exc()
    print "=============================================================="
    sys.exit(1)

