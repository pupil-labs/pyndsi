/*
 * video_stream.cpp
 *
 *  Created on: 2017/03/08
 *      Author: saki
 */

#if 1	// set 0 if you need debug log, otherwise set 1
	#ifndef LOG_NDEBUG
		#define LOG_NDEBUG
	#endif
	#undef USE_LOGALL
#else
//	#define USE_LOGALL
	#undef LOG_NDEBUG
	#undef NDEBUG
#endif

#include "utilbase.h"
#include "app_const.h"

extern "C" {
	#include <libavformat/avformat.h>
	#include <libavcodec/avcodec.h>
}

#include "video_stream.h"

namespace serenegiant {
namespace media {

VideoStream::VideoStream(const AVCodecContext *_codec_context,
	const uint32_t &_width, const uint32_t &_height, const int &_fps)
:	MediaStream(),
	codec_context(_codec_context),
	width(_width), height(_height), fps(_fps) {

	ENTER();

	EXIT();
}

VideoStream::~VideoStream() {

	ENTER();

	EXIT();
}

int VideoStream::init_stream(AVFormatContext *format_context,
	const enum AVCodecID &codec_id, AVStream *stream) {

	ENTER();

	int result = 0;

//	avcodec_parameters_from_context(stream->codecpar, codec_context);

	AVCodecParameters *params = stream->codecpar;

	params->codec_id = codec_id;
	params->codec_type = AVMEDIA_TYPE_VIDEO;
	params->width = width;
	params->height = height;
	if (!params->extradata_size && !params->extradata) {
		const size_t sz = params->extradata_size = codec_context->extradata_size;
		uint8_t *extradata = NULL;
		if (sz) {
			extradata = (uint8_t *)av_malloc(sz + AV_INPUT_BUFFER_PADDING_SIZE);
			memcpy(extradata, codec_context->extradata, sz);
		}
		params->extradata = extradata;
	} else {
		LOGD("extradata was already set:%s",
			bin2hex(params->extradata,
				(params->extradata_size > 32 ? 32 : params->extradata_size)).c_str());
	}

	stream->time_base = (AVRational) {1, fps };

	RETURN(result ,int);
}

} /* namespace media */
} /* namespace serenegiant */
