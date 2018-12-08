
package org.kivy.android;

import android.os.SystemClock;

import java.io.InputStream;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.File;

import android.app.*;
import android.content.*;
import android.view.*;
import android.view.ViewGroup;
import android.app.Activity;
import android.util.Log;
import android.widget.Toast;
import android.os.Bundle;

import android.widget.AbsoluteLayout;
import android.view.ViewGroup.LayoutParams;

import android.webkit.WebViewClient;
import android.webkit.WebView;
import android.webkit.WebSettings;

public class PythonActivity extends Activity {

    private static final String TAG = "Python";
    private WebView mWebView;
    private Thread mPythonThread;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        Log.v(TAG, "onCreate running");

        Log.v(TAG, "Device: " + android.os.Build.DEVICE);
        Log.v(TAG, "Model: " + android.os.Build.MODEL);
        super.onCreate(savedInstanceState);

        String mApkDir = getPackageCodePath().toString();
        String mAssetsDir = mApkDir + "/assets";
        String mFilesDir = getFilesDir().getAbsolutePath();
		String mCacheDir = getCacheDir().getAbsolutePath();

		System.loadLibrary("python2.7");
		System.loadLibrary("main");

        // Set up the webview
        mWebView = new WebView(this);
		WebSettings mWebSettings = mWebView.getSettings();
        mWebSettings.setJavaScriptEnabled(true);
        mWebSettings.setDomStorageEnabled(true);
		mWebSettings.setAllowUniversalAccessFromFileURLs(true);
        mWebView.loadUrl("file:///android_asset/bootstrap.html");

        mWebView.setLayoutParams(new LayoutParams(LayoutParams.FILL_PARENT, LayoutParams.FILL_PARENT));
        mWebView.setWebViewClient(new WebViewClient() {
                @Override
                public boolean shouldOverrideUrlLoading(WebView view, String url) {
					// Do not do this. It is unnecessary and it turns location.replace() into location =.
                    //view.loadUrl(url);
                    return false;
                }
            });

    	ViewGroup mLayout = new AbsoluteLayout(this);
        mLayout.addView(mWebView);
        setContentView(mLayout);

        /* start.c will chdir() to ANDROID_FILESDIR
           assets/bootstrap.py uses ANDROID_APKDIR refer to files zipped into the APK
           assets/bootstrap.py uses ANDROID_PACKAGE_NAME to recognize requests from our webview 
           assets/bootstrap_so.py uses ANDROID_CACHEDIR as a place to unpack .so files
        */
        PythonActivity.nativeSetEnv("ANDROID_APKDIR", mApkDir);
        PythonActivity.nativeSetEnv("ANDROID_FILESDIR", mFilesDir);
        PythonActivity.nativeSetEnv("ANDROID_CACHEDIR", mCacheDir);
		PythonActivity.nativeSetEnv("ANDROID_PACKAGE_NAME", getApplicationContext().getPackageName());

		/* So Python can find its standard library */
        PythonActivity.nativeSetEnv("PYTHONHOME", mAssetsDir + "/python");

		/* So Python can find bootstrap.py */
        PythonActivity.nativeSetEnv("PYTHONPATH", mAssetsDir);

		/* So start.c can later call .loadUrl() */
		nativeCallbackSetup();

		/* Start the Python interpreter thread */
        mPythonThread = new Thread(new PythonMain(), "PythonThread");
        mPythonThread.start();
    }

	/* This is called from bootstrap.py as android.loadUrl().
       It does this once it knows the URL of the WSGI server.
       Until then the webview displays assets/bootstrap.html.
    */
	public void loadUrl(final String url) {
		Log.i(TAG, "PythonActivity.loadUrl(\"" + url + "\")");
		runOnUiThread(new Runnable () {
			public void run() {
				mWebView.loadUrl(url);
			}
		});
	}

    @Override
    public void onDestroy() {
        Log.i(TAG, "onDestroy");
        super.onDestroy();

		/* All data is nearby, drop the HTTP cache. */
		mWebView.clearCache(true);

        // FIXME: mPythonThread.stop() does not work. Why?
        android.os.Process.killProcess(android.os.Process.myPid());
    }

    /**
     * Show an error using a toast. (Only makes sense from non-UI threads.)
     */
    public void toastError(final String msg) {

        final Activity thisActivity = this;

        runOnUiThread(new Runnable () {
            public void run() {
                Toast.makeText(thisActivity, msg, Toast.LENGTH_LONG).show();
            }
        });

        // Wait to show the error.
        synchronized (this) {
            try {
                this.wait(1000);
            } catch (InterruptedException e) {
				/* ignore */
            }
        }
    }

	/* Stop JavaScript timers while the application is paused */
    @Override
    protected void onPause() {
        Log.d(TAG, "onPause");
        super.onPause();
        mWebView.onPause();
        mWebView.pauseTimers();
    }

    @Override
    protected void onResume() {
        Log.d(TAG, "onResume");
        super.onResume();
        mWebView.onResume();
        mWebView.resumeTimers();
    }

	/* When the user presses the back button, go back in the webview.
       If the webview history is empty, close the app if he presses
	   back again within two seconds. */
    long lastBackClick = 0;
    @Override
    public void onBackPressed() {
        Log.d(TAG, "onBackPressed");
        if (mWebView.canGoBack()) {
            mWebView.goBack();
        } else {
			if (SystemClock.elapsedRealtime() - lastBackClick > 2000) {
				Toast.makeText(this, "Back again to close the app", Toast.LENGTH_LONG).show();
			} else {
				super.onBackPressed();
			}
        	lastBackClick = SystemClock.elapsedRealtime();
		}
    }

	/* So start.c can get a reference to PythonActivity and later call .loadUrl() */
	public native void nativeCallbackSetup();

    /* Sets an environment variable for use by the Python interpreter */
    public static native void nativeSetEnv(String j_name, String j_value);

    /* Starts the Python interpreter */
    public static native int nativeInit();
}

/* Python interpreter runs in this thread */
class PythonMain implements Runnable {
    @Override
    public void run() {
        PythonActivity.nativeInit();
    }
}

