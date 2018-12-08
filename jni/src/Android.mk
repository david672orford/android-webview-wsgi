LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE := main

# LOCAL_C_INCLUDES := $(LOCAL_PATH)/$(SDL_PATH)/include

# Add your application source files here...
LOCAL_SRC_FILES := start.c pyjniusjni.c

LOCAL_CFLAGS += -I$(LOCAL_PATH)/../../python-install/include/python2.7 $(EXTRA_CFLAGS)

LOCAL_SHARED_LIBRARIES := python_shared

LOCAL_LDLIBS := -llog -lpython2.7 $(EXTRA_LDLIBS)

LOCAL_LDFLAGS += -L$(LOCAL_PATH)/../../python-install/lib $(APPLICATION_ADDITIONAL_LDFLAGS)

include $(BUILD_SHARED_LIBRARY)

