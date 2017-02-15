/*
 * h264_decoder.cpp
 *
 *  Created on: 2017/01/26
 *      Author: saki
 */

#include "utilbase.h"

#include "h264_decoder.h"

namespace serenegiant {
namespace media {

H264Decoder::H264Decoder(const color_format_t &_color_format)
:	color_format(AV_PIX_FMT_YUV420P),
	codec(NULL), codec_context(NULL),
	src(NULL), dst(NULL),
	sws_context(NULL),
	frame_ready(false)
{
	ENTER();

	av_log_set_level(AV_LOG_VERBOSE);

	switch (_color_format) {
	case COLOR_FORMAT_YUV422:
		color_format = AV_PIX_FMT_YUV422P;
		break;
	case COLOR_FORMAT_RGB565LE:
		color_format = AV_PIX_FMT_RGB565LE;
		break;
	case COLOR_FORMAT_BGR32:
		color_format = AV_PIX_FMT_BGR32;
		break;
	default:
		color_format = AV_PIX_FMT_YUV422P;
		break;
	}

	codec = avcodec_find_decoder(AV_CODEC_ID_H264);
	codec_context = avcodec_alloc_context3(codec);
	codec_context->pix_fmt = AV_PIX_FMT_YUV420P;
	codec_context->flags2 |= CODEC_FLAG2_CHUNKS;

	src = av_frame_alloc();
	dst = av_frame_alloc();

	avcodec_open2(codec_context, codec, NULL);

	EXIT();
}

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
	if (sws_context) {
		sws_freeContext(sws_context);
		sws_context = NULL;
	}

	EXIT();
}

void H264Decoder::reinitialize_scaling_context() {
	ENTER();

	if (sws_context) {
		sws_freeContext(sws_context);
		sws_context = NULL;
	}

	EXIT();
}

int H264Decoder::set_input_buffer(uint8_t *nal_units, const size_t &bytes, const int64_t &presentation_time_us) {

	ENTER();

	int result = -1;

	AVPacket packet;

	av_init_packet(&packet);
	packet.data = nal_units;
	packet.size = bytes;
	packet.pts = presentation_time_us;

	int frame_finished = 0;
	result = avcodec_decode_video2(codec_context, src, &frame_finished, &packet);
	if (frame_finished) {
		frame_ready = true;
	}

	// you may need to free your data buffer(nal_units) here.

	RETURN(result, int);
}

int H264Decoder::get_output_buffer(uint8_t *buf, const size_t &capacity, int64_t &result_pts) {

	ENTER();

	result_pts = AV_NOPTS_VALUE;
	size_t result = get_output_bytes();

	if (LIKELY(capacity >= result)) {
		if (color_format == codec_context->pix_fmt) {
			LOGW("memcopy");
			memcpy(src->data, buf, result);
		} else {
			const int width = this->width();
			const int height = this->height();
			if (UNLIKELY(!sws_context)) {
				sws_context = sws_getContext(width, height, codec_context->pix_fmt,
					width, height, color_format, SWS_FAST_BILINEAR, NULL, NULL, NULL);
			}
			avpicture_fill((AVPicture *)dst, buf, color_format, width, height);
			sws_scale(sws_context, (const uint8_t **)src->data, src->linesize, 0, height,
				dst->data, dst->linesize);
		}
		frame_ready = false;
		result_pts = src->pkt_pts;
		if (UNLIKELY(result_pts == AV_NOPTS_VALUE)) {
			LOGW("No PTS");
		}
	} else {
		LOGE("capacity is smaller than required");
		result = -1;
	}

	RETURN(result, int);
}

}	// namespace media
}	// namespace serenegiant