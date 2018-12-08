#define PY_SSIZE_T_CLEAN
#include "Python.h"
#ifndef Py_PYTHON_H
#error Python headers needed to compile C extensions, please install development version of Python.
#else

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <dirent.h>
#include <jni.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <errno.h>

#include "android/log.h"

const char *log_tag = "python";

/*====================================
** Callbacks to Java
** See:
** http://journals.ecs.soton.ac.uk/java/tutorial/native1.1/implementing/method.html
**==================================*/

struct {
  JNIEnv*   uienv;
  JNIEnv*   pyenv;
  jobject   obj;
  jmethodID loadUrl;
  } pythonActivity;

void Java_org_kivy_android_PythonActivity_nativeCallbackSetup(JNIEnv* env, jobject obj)
{
  __android_log_print(ANDROID_LOG_INFO, log_tag, "Setting up C callbacks...");
  pythonActivity.uienv = env;
  pythonActivity.obj = (*env)->NewGlobalRef(env, obj);
  pythonActivity.loadUrl = (*env)->GetMethodID(env, (*env)->GetObjectClass(env, obj), "loadUrl", "(Ljava/lang/String;)V");
  if(pythonActivity.loadUrl == 0) {
    __android_log_print(ANDROID_LOG_FATAL, log_tag, "Failed to find loadUrl in PythonActivity");
  }
  __android_log_print(ANDROID_LOG_INFO, log_tag, "C callbacks ready");
}

/*=====================================
** android.log()
**===================================*/

static PyObject *android_log(PyObject *self, PyObject *args) {
  char *logstr;
  if (!PyArg_ParseTuple(args, "s", &logstr))
    return NULL;
  __android_log_write(ANDROID_LOG_INFO, log_tag, logstr);
  Py_RETURN_NONE;
}

static PyObject *android_load_url(PyObject *self, PyObject *args) {

  /* Convert URL from a Python string to a C string */
  char *url;
  if (!PyArg_ParseTuple(args, "s", &url))
    return NULL;
  __android_log_print(ANDROID_LOG_INFO, log_tag, "android.load_url(\"%s\")", url);

  /* Convert URL from a C string to a Java string */
  jstring jurl = (*pythonActivity.pyenv)->NewStringUTF(pythonActivity.pyenv, url);

  /* Call the .loadUrl() method in PythonActivity */
  (*pythonActivity.pyenv)->CallVoidMethod(pythonActivity.pyenv, pythonActivity.obj, pythonActivity.loadUrl, jurl);

  Py_RETURN_NONE;
}

static PyMethodDef AndroidMethods[] = {
    {"log", android_log, METH_VARARGS, "Send message to Android log"},
    {"load_url", android_load_url, METH_VARARGS, "Load a URL in the webview"},
    {NULL, NULL, 0, NULL}
	};

/* In Python 3 it is more complicated */
#if PY_MAJOR_VERSION >= 3
PyMODINIT_FUNC initandroid(void) {
  static struct PyModuleDef android = {
  	PyModuleDef_HEAD_INIT,
  	"android",
  	"",
  	-1,
  	AndroidMethods
  	};
  return PyModule_Create(&android);
}
#endif

/*====================================
** Run the Python interpreter
**==================================*/
JNIEXPORT void JNICALL Java_org_kivy_android_PythonActivity_nativeInit(JNIEnv* env, jclass cls)
{
  __android_log_print(ANDROID_LOG_INFO, log_tag, "Starting C bootstrap...");
  pythonActivity.pyenv = env;

  {
    char *filesdir = getenv("ANDROID_FILESDIR");
    if(chdir(filesdir) == -1) {
  	__android_log_print(ANDROID_LOG_FATAL, log_tag, "Failed to change to directory %s: errno=%d (%s)", filesdir, errno, strerror(errno));
  	return;
    }
  }

  __android_log_print(ANDROID_LOG_INFO, log_tag, "Initialized Python interpreter");

  /* In Python 3 the new builtins are added before interpreter initialization. */
#if PY_MAJOR_VERSION >= 3
  PyImport_AppendInittab("android", initandroid);
#endif

  Py_Initialize();
  PyEval_InitThreads();

  /* In Python 2 the new builtins are added after interpreter initialization. */
#if PY_MAJOR_VERSION < 3
  Py_InitModule("android", AndroidMethods);
#endif

  {
      __android_log_print(ANDROID_LOG_INFO, log_tag, "Running assets/bootstrap.py...");
      PyObject* module = PyImport_AddModule("__main__");
      PyObject* dict = PyModule_GetDict(module);
      PyObject* compileRetval = PyRun_String(
          "import runpy\n"
          "runpy.run_module('bootstrap')\n",
    	    Py_file_input, dict, dict
          );
      if(PyErr_Occurred()) {
          PyObject *ptype, *pvalue, *ptraceback;
          PyErr_Fetch(&ptype, &pvalue, &ptraceback);
          char *pStrErrorMessage = PyString_AsString(pvalue);
          __android_log_print(ANDROID_LOG_FATAL, log_tag, "Exception in assets/bootstrap.py: %s", pStrErrorMessage);
      }
  }

  __android_log_print(ANDROID_LOG_INFO, log_tag, "Python thread exiting.");
  Py_Finalize();
}

/*===========================================
** Java code uses this to set environment
** variables for our use.
**=========================================*/
JNIEXPORT void JNICALL Java_org_kivy_android_PythonActivity_nativeSetEnv(
                                    JNIEnv* env, jclass jcls,
                                    jstring j_name, jstring j_value)
{
    jboolean iscopy;
    const char *name = (*env)->GetStringUTFChars(env, j_name, &iscopy);
    const char *value = (*env)->GetStringUTFChars(env, j_value, &iscopy);
    setenv(name, value, 1);
    (*env)->ReleaseStringUTFChars(env, j_name, name);
    (*env)->ReleaseStringUTFChars(env, j_value, value);
}

#endif
