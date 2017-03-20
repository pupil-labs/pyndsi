/*
 * ffmpeg_utils.h
 *
 *  Created on: 2017/03/08
 *      Author: saki
 */

#ifndef UTILS_FFMPEG_UTILS_H_
#define UTILS_FFMPEG_UTILS_H_

#include <string>

extern "C" {
	#include <libavformat/avformat.h>
	#include <libavcodec/avcodec.h>
	#include <libswscale/swscale.h>
	#include <libavutil/timestamp.h>
}

namespace serenegiant {
namespace media {

std::string av_error(const int errnum);
std::string av_ts2string(const int64_t ts);
std::string av_ts2time_string(const int64_t ts, AVRational *tb);
void log_packet(const AVFormatContext *format_context, const AVPacket *packet);

}	// namespace media
}	// namespace serenegiant

#endif /* UTILS_FFMPEG_UTILS_H_ */
