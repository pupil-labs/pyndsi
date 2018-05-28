/*
 * h264_decoder.cpp
 *
 *  Created on: 2017/01/26
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

#include <string>

#include "utilbase.h"
#include "h264_utils.h"
#include "ffmpeg_utils.h"

#include "h264_decoder.h"

namespace serenegiant {
namespace media {

/*public*/
H264Decoder::H264Decoder(const color_format_t &_color_format)
:	color_format(AV_PIX_FMT_YUV420P),
	codec_context(NULL),
	src(NULL), dst(NULL),
	sws_context(NULL),
	frame_ready(false)
{
	ENTER();

	switch (_color_format) {
	case COLOR_FORMAT_YUV422:
		color_format = AV_PIX_FMT_YUV422P;
		break;
	case COLOR_FORMAT_YUV420:
		color_format = AV_PIX_FMT_YUV420P;
		break;
	case COLOR_FORMAT_RGB565LE:
		color_format = AV_PIX_FMT_RGB565LE;
		break;
	case COLOR_FORMAT_BGR32:
		color_format = AV_PIX_FMT_BGR32;
		break;
	default:
		color_format = AV_PIX_FMT_YUV420P;
		break;
	}

	avcodec_register_all();
	struct AVCodec *codec = avcodec_find_decoder(AV_CODEC_ID_H264);
	if (LIKELY(codec)) {
		codec_context = avcodec_alloc_context3(codec);
		if (LIKELY(codec_context)) {
			codec_context->pix_fmt = color_format;
			codec_context->flags2 |= AV_CODEC_FLAG2_CHUNKS;
			if (codec->capabilities & AV_CODEC_CAP_TRUNCATED) {
				codec_context->flags |= AV_CODEC_FLAG_TRUNCATED;
			}
			int result = avcodec_open2(codec_context, codec, NULL);
			if (LIKELY(!result)) {
				src = av_frame_alloc();
				dst = av_frame_alloc();
			} else {
				LOGE("avcodec_open2 failed with error %d:%s", result, av_error(result).c_str());
				avcodec_close(codec_context);
				av_free(codec_context);
				codec_context = NULL;
			}
		}
		else
			LOGE("Could not initialize codec context");
	}
	else
		LOGE("Could not find codec");

	EXIT();
}

/*virtual*/
/*public*/
H264Decoder::~H264Decoder() {

	ENTER();

	if (codec_context) {
		avcodec_close(codec_context);
		av_free(codec_context);
		codec_context = NULL;
	}
	if (src) {
		av_free(src);
		src = NULL;
	}
	if (dst) {
		av_free(dst);
		dst = NULL;
	}

	EXIT();
}

/*public*/
int H264Decoder::set_input_buffer(uint8_t *nal_units, const size_t &bytes, const int64_t &presentation_time_us) {

	ENTER();

	int result = -1;

	if (UNLIKELY(!is_initialized())) RETURN(result, int);

	AVPacket packet;

	av_init_packet(&packet);
	packet.data = nal_units;
	packet.size = bytes;
	packet.pts = presentation_time_us;

#if USE_NEW_AVCODEC_API
	result = avcodec_send_packet(codec_context, &packet);
	if (!result) {
		for ( ; !result ; ) {
			result = avcodec_receive_frame(codec_context, src);
			if (!result) {
				LOGD("got frame");
				frame_ready = true;
				// FIXME avcodec_send_packet may generate multiple frames.
				// But current implementation handle only one...will lost some of them or get stuck.
				// If you need all frames, get them and put them into queue and handle them on other thread.
				break;
			} else if ((result < 0) && (result != AVERROR(EAGAIN)) && (result != AVERROR_EOF)) {
				LOGE("avcodec_receive_frame returned error %d:%s", result, av_error(result).c_str());
			} else {
				switch (result) {
				case AVERROR(EAGAIN):
					// decoded frame not ready yet
					LOGV("avcodec_receive_frame EAGAIN");
					result = 0;
					goto ret;
				case AVERROR_EOF:
					// buffer flushed
					LOGV("avcodec_receive_frame AVERROR_EOF");
					result = 0;
					goto ret;
				default:
					LOGE("avcodec_receive_frame returned error %d:%s", result, av_error(result).c_str());
					break;
				}
			}
		}
	} else {
		switch (result) {
		case AVERROR(EAGAIN):
			LOGE("avcodec_send_packet EAGAIN");
			break;
		case AVERROR_EOF:
			LOGE("avcodec_send_packet AVERROR_EOF");
			result = 0;
			break;
		default:
			LOGE("avcodec_send_packet returned error %d:%s", result, av_error(result).c_str());
			break;
		}
	}
ret:
#else
	int frame_finished = 0;
	result = avcodec_decode_video2(codec_context, src, &frame_finished, &packet);
	if (result >= 0) {
		if (frame_finished) {
			LOGD("got frame");
			frame_ready = true;
		}
		result = 0;
	}
#endif
	RETURN(result, int);
}

/*public*/
int H264Decoder::get_output_buffer(uint8_t *result_buf, const size_t &capacity, int64_t &result_pts) {

	ENTER();

	if (UNLIKELY(!is_initialized())) RETURN(-1, int);

	result_pts = AV_NOPTS_VALUE;
	size_t result = get_output_bytes();

	if (LIKELY(capacity >= result)) {
		const int width = this->width();
		const int height = this->height();

		LOGD("Wanted format: %s", av_pix_fmt_desc_get(color_format)->name);
		LOGD("Given format: %s", av_pix_fmt_desc_get(codec_context->pix_fmt)->name);

		if (color_format == codec_context->pix_fmt) {
			LOGD("No conversion needed. Copy buffer.");
//			memcpy(result_buf, src->data[0], result);	// simple copy does not work well
#if USE_NEW_AVCODEC_API
			av_image_copy_to_buffer(result_buf,
				(int)capacity, (const uint8_t * const *)src->data, src->linesize, color_format, width, height, 1);
#else
			avpicture_layout((const AVPicture *)src, color_format, width, height, result_buf, (int)capacity);
#endif
		} else {
			LOGD("Conversion needed.");
			sws_context = sws_getCachedContext(sws_context, width, height, codec_context->pix_fmt,
			                                   width, height, color_format, SWS_FAST_BILINEAR, NULL, NULL, NULL);

#if USE_NEW_AVCODEC_API
			av_image_fill_arrays(dst->data, dst->linesize,
				result_buf, color_format, width, height, 1);
#else
			avpicture_fill((AVPicture *)dst, result_buf, color_format, width, height);
#endif
			sws_scale(sws_context, src->data, src->linesize, 0, height,
				dst->data, dst->linesize);
		}
		frame_ready = false;
#if USE_NEW_AVCODEC_API
		result_pts = src->pts; // this is always AV_NOPTS_VALUE
#else
		result_pts = src->pkt_pts;
#endif
		LOGD("%dx%d,pts=%ld", src->width, src->height, result_pts);
		if (UNLIKELY(result_pts == AV_NOPTS_VALUE)) {
			LOGD("No PTS");
		}
	} else {
		LOGE("capacity is smaller than required");
		result = -1;
	}

	RETURN(result, int);
}

}	// namespace media
}	// namespace serenegiant
