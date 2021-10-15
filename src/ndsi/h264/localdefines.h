/*
 * localdefines.h
 *
 *      Author: saki
 */

#ifndef LOCALDEFINES_H_
#define LOCALDEFINES_H_

#ifndef LOG_TAG
#define LOG_TAG "ffmpegDecoder"
#endif

#define THREAD_PRIORITY_DEFAULT         0
#define THREAD_PRIORITY_LOWEST          19
#define THREAD_PRIORITY_BACKGROUND      10
#define THREAD_PRIORITY_FOREGROUND      -2
#define THREAD_PRIORITY_DISPLAY         -4
#define THREAD_PRIORITY_URGENT_DISPLAY  -8
#define THREAD_PRIORITY_AUDIO           -16
#define THREAD_PRIORITY_URGENT_AUDIO    -19

#define USE_LOGALL  // If you don't need to all LOG, comment out this line and select follows
//#define USE_LOGV
//#define USE_LOGD
#define USE_LOGI
#define USE_LOGW
#define USE_LOGE
#define USE_LOGF

#ifdef NDEBUG
#undef USE_LOGALL
#endif

#ifdef LOG_NDEBUG
#undef USE_LOGALL
#endif


#endif /* LOCALDEFINES_H_ */
