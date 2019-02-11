/*
 * video_stream.h
 *
 *  Created on: 2017/03/08
 *      Author: saki
 */

#ifndef VIDEO_STREAM_H_
#define VIDEO_STREAM_H_

#include "media_stream.h"

namespace serenegiant {
namespace media {

class VideoStream: public virtual MediaStream {
private:
	AVCodecContext *codec_context;
	const uint32_t width, height;
	const int fps;
	bool own_context;
protected:
	virtual int init_stream(AVFormatContext *format_context,
		const enum AVCodecID &codec_id, AVStream *stream);
public:
	// to ease to handle(get) codec specific data(sps/pps for h.264),
	// pass AVCodecContext instance to this constructor
	VideoStream(const uint32_t &width, const uint32_t &height, const int &fps = 30);
	VideoStream(AVCodecContext *codec_context,
		const uint32_t &width, const uint32_t &height, const int &fps = 30);
	virtual ~VideoStream();
};

} /* namespace media */
} /* namespace serenegiant */

#endif /* VIDEO_STREAM_H_ */
