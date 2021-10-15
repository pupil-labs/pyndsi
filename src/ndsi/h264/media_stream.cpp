/*
 * media_stream.cpp
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
#include "h264_utils.h"
#include "ffmpeg_utils.h"

#include "media_stream.h"

namespace serenegiant {
namespace media {

/*public*/
MediaStream::MediaStream()
:	stream(NULL),
	first_pts_us(0),
	frames(0) {

	ENTER();

	EXIT();
}

/*virtual*/
/*public*/
MediaStream::~MediaStream() {

	ENTER();

	release();

	EXIT();
}

/*virtual*/
/*public*/
void MediaStream::release() {

	ENTER();

	LOGI("total input %u frames", frames);

	EXIT();
}

/*protected/friend*/
int MediaStream::init(AVFormatContext *format_context, const enum AVCodecID &codec_id) {

	ENTER();

	int result = -1;

	if (!stream) {
		first_pts_us = 0;
		frames = 0;
		stream = avformat_new_stream(format_context, NULL);
		if (LIKELY(stream)) {
			stream->id = format_context->nb_streams - 1;
			result = init_stream(format_context, codec_id, stream);
		} else {
			LOGE("avformat_new_stream failed, errno=%d", errno);
		}
	} else {
		LOGE("already initialized");
	}

	RETURN(result, int);
}

int MediaStream::set_input_buffer(AVFormatContext *output_context,
	const uint8_t *nal_units, const size_t &bytes, const int64_t &presentation_time_us) {

//	ENTER();

	int result = 0;
	AVPacket packet;
#if !defined(_MSC_VER)
	static AVRational time_base = (AVRational){1, 1000000};
#else
	static AVRational time_base;
	time_base.num = 1;
	time_base.den = 1000000;
#endif

	av_init_packet(&packet);
	packet.flags |= (get_vop_type_annexb(nal_units, bytes) >= 0 ? AV_PKT_FLAG_KEY : 0);
	packet.data = (uint8_t *)nal_units;
	packet.size = bytes;
	packet.pts = packet.dts = presentation_time_us;
	av_packet_rescale_ts(&packet, time_base, stream->time_base);
	packet.stream_index = stream->index;

	if (UNLIKELY((frames % 100) == 0)) {
		LOGI("input %u frames", frames);
		log_packet(output_context, &packet);
	}
	frames++;

	result = av_interleaved_write_frame(output_context, &packet);

	return result; // RETURN(result, int);
}

} /* namespace media */
} /* namespace serenegiant */
