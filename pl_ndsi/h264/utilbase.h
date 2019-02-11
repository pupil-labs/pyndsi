/*
 * utilsbase.h
 *
 *  Created on: 2017/01/24
 *      Author: saki
 */

#ifndef UTILBASE_H_
#define UTILBASE_H_

#include <stddef.h>

#if defined(_MSC_VER)
//	#include "windows/unistd.h"
	#define basename(x) ((x))

#else
	#include <unistd.h>
	#include <libgen.h>
#endif
#include <stdio.h>
#include <sys/types.h>

#include "localdefines.h"

#define		SAFE_FREE(p)				{ if (p) { free((p)); (p) = NULL; } }
#define		SAFE_DELETE(p)				{ if (p) { delete (p); (p) = NULL; } }
#define		SAFE_DELETE_ARRAY(p)		{ if (p) { delete [](p); (p) = NULL; } }
#define		NUM_ARRAY_ELEMENTS(p)		((int) sizeof(p) / sizeof(p[0]))

#if defined(__GNUC__)
// the macro for branch prediction optimaization for gcc(-O2/-O3 required)
#define		CONDITION(cond)				((__builtin_expect((cond)!=0, 0)))
#define		LIKELY(x)					((__builtin_expect(!!(x), 1)))	// x is likely true
#define		UNLIKELY(x)					((__builtin_expect(!!(x), 0)))	// x is likely false
#else
#define		CONDITION(cond)				((cond))
#define		LIKELY(x)					((x))
#define		UNLIKELY(x)					((x))
#endif

#include <assert.h>
#define CHECK(CONDITION) { bool RES = (CONDITION); assert(RES); }
#define CHECK_EQ(X, Y) { bool RES = (X == Y); assert(RES); }
#define CHECK_NE(X, Y) { bool RES = (X != Y); assert(RES); }
#define CHECK_GE(X, Y) { bool RES = (X >= Y); assert(RES); }
#define CHECK_GT(X, Y) { bool RES = (X > Y); assert(RES); }
#define CHECK_LE(X, Y) { bool RES = (X <= Y); assert(RES); }
#define CHECK_LT(X, Y) { bool RES = (X < Y); assert(RES); }

#if defined(USE_LOGALL) && !defined(LOG_NDEBUG)
	#define LOGV(FMT, ...) fprintf(stderr, "[V/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
	#define LOGD(FMT, ...) fprintf(stderr, "[D/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
	#define LOGI(FMT, ...) fprintf(stderr, "[I/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
	#define LOGW(FMT, ...) fprintf(stderr, "[W/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
	#define LOGE(FMT, ...) fprintf(stderr, "[E/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
	#define LOGF(FMT, ...) fprintf(stderr, "[F/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
	#define LOGV_IF(cond, ...) ( (CONDITION(cond)) ? LOGV(__VA_ARGS__) : (0) )
	#define LOGD_IF(cond, ...) ( (CONDITION(cond)) ? LOGD(__VA_ARGS__) : (0) )
	#define LOGI_IF(cond, ...) ( (CONDITION(cond)) ? LOGI(__VA_ARGS__) : (0) )
	#define LOGW_IF(cond, ...) ( (CONDITION(cond)) ? LOGW(__VA_ARGS__) : (0) )
	#define LOGE_IF(cond, ...) ( (CONDITION(cond)) ? LOGE(__VA_ARGS__) : (0) )
	#define LOGF_IF(cond, ...) ( (CONDITION(cond)) ? LOGF(__VA_ARGS__) : (0) )
#else
	#if defined(USE_LOGV) && !defined(LOG_NDEBUG)
		#define LOGV(FMT, ...) fprintf(stderr, "[V/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
		#define LOGV_IF(cond, ...) ( (CONDITION(cond)) ? LOGV(__VA_ARGS__) : (0) )
		#else
		#define LOGV(...)
		#define LOGV_IF(cond, ...)
	#endif
	#if defined(USE_LOGD) && !defined(LOG_NDEBUG)
		#define LOGD(FMT, ...) fprintf(stderr, "[D/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
		#define LOGD_IF(cond, ...) ( (CONDITION(cond)) ? LOGD(__VA_ARGS__) : (0) )
	#else
		#define LOGD(...)
		#define LOGD_IF(cond, ...)
	#endif
	#if defined(USE_LOGI)
		#define LOGI(FMT, ...) fprintf(stderr, "[I/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
		#define LOGI_IF(cond, ...) ( (CONDITION(cond)) ? LOGI(__VA_ARGS__) : (0) )
	#else
		#define LOGI(...)
		#define LOGI_IF(cond, ...)
	#endif
	#if defined(USE_LOGW)
		#define LOGW(FMT, ...) fprintf(stderr, "[W/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
		#define LOGW_IF(cond, ...) ( (CONDITION(cond)) ? LOGW(__VA_ARGS__) : (0) )
	#else
		#define LOGW(...)
		#define LOGW_IF(cond, ...)
	#endif
	#if defined(USE_LOGE)
		#define LOGE(FMT, ...) fprintf(stderr, "[E/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
		#define LOGE_IF(cond, ...) ( (CONDITION(cond)) ? LOGE(__VA_ARGS__) : (0) )
	#else
		#define LOGE(...)
		#define LOGE_IF(cond, ...)
	#endif
	#if defined(USE_LOGF)
#define LOGF(FMT, ...) fprintf(stderr, "[F/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
		#define LOGF_IF(cond, ...) ( (CONDITION(cond)) ? LOGF(__VA_ARGS__) : (0) )
	#else
		#define LOGF(...)
		#define LOGF_IF(cond, ...)
	#endif
#endif

#ifndef		LOG_ALWAYS_FATAL_IF
#define		LOG_ALWAYS_FATAL_IF(cond, ...) ( (CONDITION(cond)) ? ((void)__android_log_assert(#cond, LOG_TAG, ## __VA_ARGS__)) : (void)0 )
#endif

//#ifndef		LOG_ALWAYS_FATAL
//#define		LOG_ALWAYS_FATAL(...) ( ((void)__android_log_assert(NULL, LOG_TAG, ## __VA_ARGS__)) )
//#endif

#ifndef		LOG_ASSERT
#define		LOG_ASSERT(cond, ...) LOG_FATAL_IF(!(cond), ## __VA_ARGS__)
#endif

#ifdef LOG_NDEBUG

#ifndef		LOG_FATAL_IF
#define		LOG_FATAL_IF(cond, ...) ((void)0)
#endif
#ifndef		LOG_FATAL
#define		LOG_FATAL(...) ((void)0)
#endif

#else

#ifndef		LOG_FATAL_IF
#define		LOG_FATAL_IF(cond, ...) LOG_ALWAYS_FATAL_IF(cond, ## __VA_ARGS__)
#endif
#ifndef		LOG_FATAL
#define		LOG_FATAL(...) LOG_ALWAYS_FATAL(__VA_ARGS__)
#endif

#endif

#define		ENTER()				LOGD("begin")
#define		RETURN(code,type)	{type RESULT = code; LOGD("end (%d)", (int)RESULT); return RESULT;}
#define		RET(code)			{LOGD("end"); return code;}
#define		EXIT()				{LOGD("end"); return;}
#define		PRE_EXIT()			LOGD("end")

#if (defined(USE_LOGALL) || defined(USE_LOGI)) && !defined(LOG_NDEBUG)
#define MARK(FMT, ...) fprintf(stderr, "[M/" LOG_TAG ":%s:%d:%s]:" FMT "\n", basename(__FILE__), __LINE__, __FUNCTION__, ## __VA_ARGS__)
#else
#define		MARK(...)
#endif

#define LITERAL_TO_STRING_INTERNAL(x)    #x
#define LITERAL_TO_STRING(x) LITERAL_TO_STRING_INTERNAL(x)

#define TRESPASS() LOG_ALWAYS_FATAL( __FILE__ ":" LITERAL_TO_STRING(__LINE__) " Should not be here.");

#endif /* UTILBASE_H_ */
