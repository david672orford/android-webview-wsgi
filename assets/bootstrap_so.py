import os, imp
tempdir = os.path.join(os.environ['ANDROID_CACHEDIR'], "lib-dynload")
if not os.path.isdir(tempdir):
    os.mkdir(tempdir)
def dynload(name,filename,loader):
    #print "dynload(): module %s was loaded from %s" % (name, filename)
    dirname, basename = os.path.split(filename)
    basename, extension = os.path.splitext(basename)
    so_tempfile = os.path.join(tempdir, basename + ".so")
    #print "dynload(): so_tempfile:", so_tempfile
    if not os.path.exists(so_tempfile):
        #print "dynload(): creating so_tempfile..."
        data = loader.get_data(os.path.join(dirname, basename + ".so"))
        with open(so_tempfile, "wb") as fh:
            fh.write(data)
    #print "dynload(): Loading so_tempfile..."
    imp.load_dynamic(name, so_tempfile)
    #print "dynload(): %s loaded" % name
