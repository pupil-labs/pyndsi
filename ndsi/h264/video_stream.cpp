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

extern "C" {
	#include <libavformat/avformat.h>
	#include <libavcodec/avcodec.h>
}

#include "video_stream.h"

namespace serenegiant {
namespace media {

AVCodecContext *default_codec() {
	avcodec_register_all();
	struct AVCodec *codec = avcodec_find_decoder(AV_CODEC_ID_H264);
	return avcodec_alloc_context3(codec);
}

VideoStream::VideoStream(const uint32_t &_width, const uint32_t &_height, const int &_fps)
:	VideoStream(default_codec(), _width, _height, _fps) {

	ENTER();

	own_context = true;

	EXIT();
}

VideoStream::VideoStream(AVCodecContext *_codec_context,
	const uint32_t &_width, const uint32_t &_height, const int &_fps)
:	MediaStream(),
	codec_context(_codec_context),
	width(_width), height(_height), fps(_fps), own_context(false) {

	ENTER();

	EXIT();
}

VideoStream::~VideoStream() {

	ENTER();

	if (own_context)
		avcodec_free_context(&codec_context);

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
	params->format = AV_PIX_FMT_YUV420P;
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

#if !defined(_MSC_VER)
	stream->time_base = (AVRational) {1, fps };
#else
	static AVRational time_base;
	time_base.num = 1;
	time_base.den = 1000;
	stream->time_base.num = 1;
	stream->time_base.den = fps;
#endif

	RETURN(result ,int);
}

} /* namespace media */
} /* namespace serenegiant */
