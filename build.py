#!/usr/bin/env python2.7

from __future__ import print_function
from os.path import dirname, join, isfile, isdir
from os import makedirs, listdir, unlink
import subprocess
import shutil
import sys
from fnmatch import fnmatch
import jinja2
import re

curdir = dirname(__file__)

# A host version of Python that matches our ARM version. We use
# this to compile .py files to .pyo files.
PYTHON = join(curdir, 'python-install', 'bin', 'python.host')

GRADLE = join(curdir, 'gradlew')

def parse_pattern_list(list_text):
    patterns = []
    for line in list_text.splitlines():
        line = line.split("#")[0].strip()
        if line != "":
            patterns.append(line)
    return patterns

WHITELIST_BASE = parse_pattern_list("""
    __future__.py
    lib-dynload/future_builtins.so
    site.py
    sysconfig.py
    config/Makefile
    os.py
    posixpath.py
    genericpath.py
    stat.py
    types.py
    _abcoll.py
    abc.py
    _weakrefset.py
    copy_reg.py
    warnings.py
    linecache.py
    UserDict.py
    zipfile.py
    struct.py
    heapq.py
    lib-dynload/_heapq.so
    bisect.py
    io.py
    lib-dynload/_io.so
    runpy.py
    pkgutil.py
    mimetools.py
    BaseHTTPServer.py
    SocketServer.py
    json/*
    lib-dynload/_json.so

    keyword.py

    shutil.py
    fnmatch.py
    re.py
    sre_compile.py
    sre_parse.py
    sre_constants.py
    collections.py
    itertools.py
    thread.py
    mimetypes.py
    urllib.py
    string.py
    socket.py
    functools.py
    urlparse.py
    tempfile.py
    random.py
    __future__.py
    math.py
    hashlib.py
    rfc822.py
    threading.py
    traceback.py
    util.py
""")

WHITELIST_ADDONS = {
    'wsgiref': ['wsgiref/*'],
    'werkzeug': parse_pattern_list("""
        site-packages/werkzeug/[!d]*.py
        site-packages/werkzeug/data*.py
        codecs.py
        StringIO.py
        inspect.py
        dis.py
        opcode.py
        tokenize.py
        token.py
        weakref.py
        encodings/__init__.py
        encodings/aliases.py
        encodings/utf_8.py
        encodings/ascii.py
        encodings/latin_1.py
        email/__init__.py
        email/utils.py
        email/_parseaddr.py
        email/encoders.py
        email/mime/__init__.py
        base64.py
        quopri.py
        urllib2.py
        httplib.py
        copy.py
        htmlentitydefs.py
        difflib.py
        uuid.py
        pprint.py
        hmac.py
        logging/*
        atexit.py
        """),
    'jinja2': parse_pattern_list("""
        site-packages/jinja2/*
        encodings/hex_codec.py            # or maybe for werkzeug
        site-packages/markupsafe/*
        decimal.py
        numbers.py
        """),
    'flask': parse_pattern_list("""
        site-packages/flask/*
        site-packages/itsdangerous/*
        cookielib.py
        calendar.py
        locale.py
        _LWPCookieJar.py
        _MozillaCookieJar.py
        """),
    }

# We tried blacklisting everything we did not want, but eventually decided that
# whitelisting what we did want was the easier approach. Though it is not used
# right now by this script, we keep the blacklist around for reference because
# it contains a lot of valuable information about what is what.
BLACKLIST_PATTERNS = parse_pattern_list("""
    # temp files
    *~
    *.bak
    *.swp

    # pyc/py
    *.pyc
    *.pyo
    *.egg-info
    *.egg-info/*
    *.dist-info/*

    # stuff we would not have expected to see
    *.c
    *.in
    *.a
    *.o

    # tests
    */testsuite/* 
    */test/*

    # documentation
    */README
    *.txt

    # unused encodings
    lib-dynload/*codec*
    encodings/cp*.py
    encodings/tis*
    encodings/shift*
    encodings/bz2*
    encodings/iso*
    encodings/undefined*
    encodings/johab*
    encodings/p*
    encodings/m*
    encodings/euc*
    encodings/k*
    encodings/unicode_internal*
    encodings/quo*
    encodings/gb*
    encodings/big5*
    encodings/hp*
    encodings/hz*

    # other unused python standard library modules
    unittest/*
    bsddb/*
    hotshot/*
    pydoc_data/*
    anydbm.py
    dummy_threading.py
    dumbdbm.py
    __phello__.foo.py
    multiprocessing/dummy*
    multiprocessing/*
    distutils/*
    idlelib/*
    lib2to3/*
    robotparser.py
    compiler/*
    plat-*
    fractions.py
    SimpleXMLRPCServer.py
    DocXMLRPCServer.py
    textwrap.py
    ssl.py
    cProfile.py
    CGIHTTPServer.py
    config/*
    doctest.py
    ctypes/*
    compileall.py
    pydoc.py
    _pyio.py            # we include the C implementation
    dircache.py
    ConfigParser.py
    htmllib.py
    HTMLParser.py
    optparse.py
    profile.py
    pstats.py
    py_compile.py
    sgmllib.py
    shlex.py
    xml/sax/*
    xml/dom/*
    xml/parsers/*
    email/message.py
    email/feedparser.py
    formatter.py
    timeit.py
    toaiff.py
    cgi*
    argparse.py
    bdb.py
    binhex.py
    gettext.py
    markupbase.py
    importlib/*
    imputil.py

    # Network protocls we probably will not need
    xmlrpclib.py
    telnetlib.py
    ftplib.py
    imaplib.py
    nntplib.py
    smtp*

    # Deprecated packages
    xmllib.py
    stringold.py
    ihooks.py
    Bastion.py

    # Unixy stuff not useful on mobile devices
    tty.py
    pty.py
    mhlib.py
    mailbox.py
    webbrowser.py
    audiodev.py

    # Wrong platform
    ntpath.py
    macpath.py
    nturl2path.py
    macurl2path.py
    os2emxpath.py

    # File formats we probably do not need
    sunau*
    wave.py
    aifc.py
    xdrlib.py
    imghdr.py
    sndhdr.py
    tarfile.py
    whichdb.py
    csv.py
    lib-dynload/_csv.*

    # Easter Eggs
    antigravity.py
    this.py

    # Unused addon packages or parts thereof
    site-packages/setuptools/*
    site-packages/pkg_resources/*
    site-packages/easy_install.py
    site-packages/werkzeug/debug/*
    site-packages/werkzeug/contrib/*
    site-packages/flask/testing.py

    # unused binaries python modules
    lib-dynload/termios.so
    lib-dynload/_lsprof.so
    lib-dynload/*audioop.so
    lib-dynload/mmap.so
    lib-dynload/_hotshot.so
    lib-dynload/grp.so                # access to /etc/group
    lib-dynload/resource.so            # system resource limits
    lib-dynload/pyexpat.so
    lib-dynload/_ctypes_test.so
    lib-dynload/_testcapi.so
    lib-dynload/syslog.so
    lib-dynload/_ctypes.so
    lib-dynload/unicodedata.so
""")

def fnmatch_list(pattern_list, name):
    for pattern in pattern_list:
        if fnmatch(name, pattern):
            return True
    return False


def listfiles(d):
    '''
    Return a list of files in a directory and its subdirectories much
    like the Unix find command.
    '''
    subdirlist = []
    for item in listdir(d):
        fn = join(d, item)
        if isfile(fn):
            yield fn
        else:
            subdirlist.append(fn)
    for subdir in subdirlist:
        for fn in listfiles(subdir):
            yield fn


def copy_files(from_dir, to_dir, whitelist=None):
    from_dir_len = len(from_dir) + 1
    for fn in listfiles(from_dir):
        fn_relative = fn[from_dir_len:]
        if whitelist is None or fnmatch_list(whitelist, fn_relative):
            to_fn = join(to_dir, fn_relative)
            to_subdir = dirname(to_fn)
            if not isdir(to_subdir):
                makedirs(to_subdir)
            print("%s -> %s" % (fn, to_fn))
            shutil.copy(fn, to_fn)


# Compile all of the .py files to .pyo files and delete the .py files to save space.
def py_to_pyo(pydir):
    subprocess.call([PYTHON, '-OO', '-m', 'compileall', pydir])
    if True:        # disable to get backtraces to work on the Android device
        for fn in listfiles(pydir):
            if fn.endswith(".py") or fn.endswith(".pyc"):
                unlink(fn)

environment = jinja2.Environment(loader=jinja2.FileSystemLoader(
    join(curdir, 'templates')))

def render_template(template, dest, **kwargs):
    '''
    Using jinja2, render `template` to the filename `dest`, supplying the
    keyword arguments as template parameters.
    '''

    dest_dir = dirname(dest)
    if dest_dir and not isdir(dest_dir):
        makedirs(dest_dir)

    template = environment.get_template(template)
    text = template.render(**kwargs)

    with open(dest, 'wb') as f:
        f.write(text.encode('utf-8'))


# Fix up the Android project so that it is ready to build.
def make_package(args):

    print("Copying Python libraries...")

    # If there there is a copy of the Python library in the assets folder
    # (presumably left over from last time), remove it.
    if isdir("assets/python"):
        shutil.rmtree("assets/python")

    # sysconfig module needs pyconfig.h
    makedirs("assets/python/include/python2.7")
    shutil.copy("python-install/include/python2.7/pyconfig.h", "assets/python/include/python2.7/pyconfig.h")    

    # The .py files go in this subdirector.
    pydest = "assets/python/lib/python2.7"

    whitelist = WHITELIST_BASE
    for module in args.modules.replace(" ","").split(","):
        whitelist.extend(WHITELIST_ADDONS[module])

    # Copy the files (whitelist and blacklist may apply)
    copy_files("python-install/lib/python2.7", pydest, whitelist)

    # Create loaders for the .so files since zipimport does not support them.
    for fn in listfiles(pydest):
        if fn.endswith(".so"):
            with open(re.sub(r"\.so$", ".py", fn), "w") as fh:
                fh.write("import bootstrap_so\nbootstrap_so.dynload(__name__,__file__,__loader__)\n")

    if not args.no_pyo:
        py_to_pyo(pydest)

    print("Copying app...")
    appdest = "assets/app"
    if isdir(appdest):
        shutil.rmtree(appdest)
    copy_files(args.wsgi_app, appdest)

    if not args.no_pyo:
        py_to_pyo(appdest)

    print("Copying images...")
    default_icon = 'templates/kivy-icon.png'
    shutil.copy(args.icon or default_icon, 'res/drawable/icon.png')

    default_presplash = 'templates/kivy-presplash.jpg'
    shutil.copy(args.presplash or default_presplash,
                'res/drawable/presplash.jpg')

    print("Rendering templates...")

    versioned_name = (args.name.replace(' ', '').replace('\'', '') + '-' + args.version)

    version_code = 0
    if not args.numeric_version:
        for i in args.version.split('.'):
            version_code *= 100
            version_code += int(i)
        args.numeric_version = str(version_code)

    render_template(
        'AndroidManifest.tmpl.xml',
        'AndroidManifest.xml',
        args=args,
        )

    render_template(
        'build.tmpl.gradle',
        'build.gradle',
        args=args,
        versioned_name=versioned_name)

    render_template(
        'strings.tmpl.xml',
        'res/values/strings.xml',
        args=args)

def parse_args(args=None):
    import argparse
    ap = argparse.ArgumentParser(description='''\
Package a Python application for Android.

For this to work, Java and Ant need to be in your path, as does the
tools directory of the Android SDK.
''')

    ap.add_argument('--wsgi-app', dest='wsgi_app',
                    help='the WSGI app files files',
                    required=True)
    ap.add_argument('--package', dest='package',
                    help=('The name of the java package the project will be'
                          ' packaged under.'),
                    required=True)
    ap.add_argument('--name', dest='name',
                    help=('The human-readable name of the project.'),
                    required=True)
    ap.add_argument('--numeric-version', dest='numeric_version',
                    help=('The numeric version number of the project. If not '
                          'given, this is automatically computed from the '
                          'version.'))
    ap.add_argument('--version', dest='version',
                    help=('The version number of the project. This should '
                          'consist of numbers and dots, and should have the '
                          'same number of groups of numbers as previous '
                          'versions.'),
                    required=True)
    ap.add_argument('--orientation', dest='orientation', default='sensor',
                    help=('The orientation that the game will display in. '
                          'Usually one of "landscape", "portrait" or '
                          '"sensor"'))
    ap.add_argument('--icon', dest='icon',
                    help='A png file to use as the icon for the application.')
    ap.add_argument('--presplash', dest='presplash',
                    help=('A jpeg file to use as a screen while the '
                          'application is loading.'))
    ap.add_argument('--window', dest='window', action='store_false',
                    help='Indicate if the application will be windowed')
    ap.add_argument('--sdk', dest='sdk_version', default=27, type=int,
                    help=('Code is compatible with this version and lower.'
                          'Defaults to 27.'))
    ap.add_argument('--minsdk', dest='min_sdk_version',
                    default=19, type=int,
                    help=('Warn if code uses features introduced after this version.'
                          'Defaults to 19.'))
    ap.add_argument('--modules', dest='modules',
                    default='wsgiref',
                    help=('Extra Python modules to include (with their dependencies)'))
    ap.add_argument('--no-pyo', dest='no_pyo', action='store_false',
                    help=('Refrain from compiling .py files to .pyo.'
                          '(For the sake of stack backtraces.)'))
                    

    args = ap.parse_args(args)

    if args.name and args.name[0] == '"' and args.name[-1] == '"':
        args.name = args.name[1:-1]

    if args.sdk_version == -1:
        args.sdk_version = args.min_sdk_version

    return args


if __name__ == "__main__":
    args = parse_args()
    make_package(args)

