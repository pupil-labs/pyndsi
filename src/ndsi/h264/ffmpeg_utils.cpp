/*
 * ffmpeg_utils.cpp
 *
 *  Created on: 2017/03/08
 *      Author: saki
 */

#include "utilbase.h"
#include "ffmpeg_utils.h"

namespace serenegiant {
namespace media {

std::string av_error(const int errnum) {
	char buf[AV_ERROR_MAX_STRING_SIZE + 1];
	av_strerror(errnum, buf, AV_ERROR_MAX_STRING_SIZE);
	buf[AV_ERROR_MAX_STRING_SIZE] = '\0';
	return std::string(buf);
}

std::string av_ts2string(const int64_t ts) {
	char buf[AV_ERROR_MAX_STRING_SIZE + 1];
	av_ts_make_string(buf, ts);
	buf[AV_ERROR_MAX_STRING_SIZE] = '\0';
	return std::string(buf);
}

std::string av_ts2time_string(const int64_t ts, AVRational *tb) {
	char buf[AV_ERROR_MAX_STRING_SIZE + 1];
	av_ts_make_time_string(buf, ts, tb);
	buf[AV_ERROR_MAX_STRING_SIZE] = '\0';
	return std::string(buf);
}

void log_packet(const AVFormatContext *format_context, const AVPacket *packet) {
    AVRational *time_base = &format_context->streams[packet->stream_index]->time_base;
    LOGV("pts:%s pts_time:%s dts:%s dts_time:%s duration:%s duration_time:%s stream_index:%d",
    	av_ts2string(packet->pts).c_str(), av_ts2time_string(packet->pts, time_base).c_str(),
		av_ts2string(packet->dts).c_str(), av_ts2time_string(packet->dts, time_base).c_str(),
		av_ts2string(packet->duration).c_str(), av_ts2time_string(packet->duration, time_base).c_str(),
		packet->stream_index);
}

}	// namespace media
}	// namespace serenegiant
