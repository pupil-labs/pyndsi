/*
 * mp4_writer.h
 *
 *  Created on: 2017/03/08
 *      Author: saki
 */

#ifndef MP4_WRITER_H_
#define MP4_WRITER_H_

#include <vector>
#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
#include <stdarg.h>

extern "C" {
	#include <libavformat/avformat.h>
	#include <libavcodec/avcodec.h>
	#include <libswscale/swscale.h>
	#include <libswresample/swresample.h>

	#include <libavutil/avassert.h>
	#include <libavutil/imgutils.h>
	#include <libavutil/channel_layout.h>
	#include <libavutil/mathematics.h>
	#include <libavutil/timestamp.h>
	#include <libavutil/opt.h>
}

namespace serenegiant {
namespace media {

class MediaStream;

class Mp4Writer {
private:
	const std::string file_name;
	AVFormatContext *format_context;
	AVOutputFormat *format;
	AVDictionary *option;
	std::vector<MediaStream *> streams;
	volatile bool is_running;

	int find_stream(const MediaStream *stream);
	void free_streams();
	MediaStream *get_stream(const int &index);
protected:
	bool write_video_frame(AVFormatContext *format_context, MediaStream &stream, AVPacket &pkt, const long &presentation_time_us);
	void close_stream(AVFormatContext *format_context, MediaStream &stream);
public:
	Mp4Writer(const std::string &file_name);
	virtual ~Mp4Writer();
	virtual void release();

	/**
	 * add MediaStream,
	 * should call this for each MediaStream before #start
	 * should not delete stream by yourself
	 * @param stream
	 * @return if success, return >= 0 as stream index, otherwise return negative value,
	 */
	virtual int add(MediaStream *stream);
	virtual int start();
	virtual void stop();
	inline const bool isRunning() const { return is_running; };

	int set_input_buffer(const int &stream_index,
		const uint8_t *nal_units, const size_t &bytes, const int64_t &presentation_time_us);
};

} /* namespace media */
} /* namespace serenegiant */

#endif /* MP4_WRITER_H_ */
