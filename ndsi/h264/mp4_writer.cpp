/*
 * mp4_writer.cpp
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
	#define USE_LOGALL
	#undef LOG_NDEBUG
	#undef NDEBUG
#endif

#include "utilbase.h"
#include "ffmpeg_utils.h"

#include "media_stream.h"
#include "video_stream.h"

#include "mp4_writer.h"

namespace serenegiant {
namespace media {

/*public*/
Mp4Writer::Mp4Writer(const std::string &_file_name)
:	file_name(_file_name),
	format_context(NULL),
	format(NULL),
	option(NULL),
	is_running(false) {

	ENTER();

	LOGV("filename=%s", file_name.c_str());
	int result = avformat_alloc_output_context2(&format_context, NULL, NULL, file_name.c_str());
	LOGV("avformat_alloc_output_context2 returned %d", result);
	if (UNLIKELY((result < 0) || !format_context)) {
		LOGW("failed to deduce output format from file extension, try mp4");
		if (format_context) {
			avformat_free_context(format_context);
			format_context = NULL;
		}
		result = avformat_alloc_output_context2(&format_context, NULL, "mp4", file_name.c_str());
		if (result < 0) {
			LOGE("avformat_alloc_output_context2 failed, err=%s", av_error(result).c_str());
		}
	}
	if (LIKELY(format_context)) {
		format = format_context->oformat;
	} else {
		LOGE("failed to create format context, result=%d", result);
	}

	EXIT();
}

/*virtual*/
/*public*/
Mp4Writer::~Mp4Writer() {
	ENTER();

	release();

	EXIT();
}

/*virtual*/
/*public*/
void Mp4Writer::release() {
	ENTER();

	stop();

	EXIT();
}

/*virtual*/
/*public*/
int Mp4Writer::add(MediaStream *stream) {

	ENTER();

	int result = -1;
	if (UNLIKELY(!format_context)) {
		LOGE("format context is null, already released?");
		goto ret;
	}
	if (LIKELY(stream)) {
		int ix = find_stream(stream);
		if (LIKELY(ix < 0)) {
			LOGV("add new stream, detect stream type");
			enum AVCodecID codec_id = AV_CODEC_ID_NONE;
			if (dynamic_cast<VideoStream *>(stream) != NULL) {
				LOGV("VideoStream");
				codec_id = format->video_codec;
			} else {
				LOGW("unknown MediaStream");
			}
			if (LIKELY(codec_id != AV_CODEC_ID_NONE)) {
				result = stream->init(format_context, codec_id);
				if (result >= 0) {
					streams.push_back(stream);
				} else {
					LOGE("failed to init stream:result=%d", result);
					SAFE_DELETE(stream);
				}
			}
		} else {
			LOGW("specific stream was already added");
			result = ix;
		}
	} else {
		LOGE("stream is null");
	}
ret:
	RETURN(result, int);
}

/*virtual*/
/*public*/
int Mp4Writer::start() {
	ENTER();

	int result = -1;
	if (UNLIKELY(!format_context || !format)) {
		LOGE("format context is null, already released?");
		goto ret;
	}
	if (LIKELY(!streams.empty())) {

		av_dump_format(format_context, 0, file_name.c_str(), 1);

		if (!(format->flags & AVFMT_NOFILE)) {
			result = avio_open(&format_context->pb, file_name.c_str(), AVIO_FLAG_WRITE);
			if (UNLIKELY(result < 0)) {
				LOGE("avio_open failed, err=%s", av_error(result).c_str());
				goto ret;
			}
		} else {
			LOGE("format is null or no output file is specified.");
			goto ret;
		}

		result = avformat_write_header(format_context, &option);
		if (UNLIKELY(result < 0)) {
			LOGE("avformat_write_header failed, err=%s", av_error(result).c_str());
			goto ret;
		}
		is_running = true;
	} else {
		LOGE("could not start because no MediaStream were added");
	}
ret:
	RETURN(result, int);
}

/*virtual*/
/*public*/
void Mp4Writer::stop() {
	ENTER();

	if (isRunning()) {
		is_running = false;
		if (LIKELY(format_context) && !streams.empty()) {
			LOGV("av_write_trailer");
			av_write_trailer(format_context);

		}
	}
	free_streams();
	if (format_context) {
		if (format && !(format->flags & AVFMT_NOFILE)) {
			avio_closep(&format_context->pb);
		}
		avformat_free_context(format_context);
		format_context = NULL;
		format = NULL;
	}

	EXIT();
}

/*public*/
int Mp4Writer::set_input_buffer(const int &stream_index,
	const uint8_t *nal_units, const size_t &bytes, const int64_t &presentation_time_us) {

//	ENTER();

	int result = -1;

	MediaStream *stream = get_stream(stream_index);
	if (LIKELY(stream)) {
		result = stream->set_input_buffer(format_context, nal_units, bytes, presentation_time_us);
	}

	return result; // RETURN(result, int);
}

/*private*/
int Mp4Writer::find_stream(const MediaStream *stream) {

	ENTER();

	int result = -1, ix = 0;
	if (!streams.empty()) {
		for (auto itr: streams) {
			if (stream == itr) {
				result = ix;
				break;
			}
			ix++;
		}
	}

	RETURN(result, int);
}

/*private*/
void Mp4Writer::free_streams() {
	ENTER();

	if (!streams.empty()) {
		for (auto itr: streams) {
			MediaStream *stream = itr;
			SAFE_DELETE(stream);
		}
		streams.clear();
		streams.shrink_to_fit();
	}

	EXIT();
}

/*private*/
MediaStream *Mp4Writer::get_stream(const int &index) {
//	ENTER();

	MediaStream *result = NULL;

	if ((index >= 0) && (index < (int)streams.size())) {
		result = streams[index];
	}

	return result; // RET(result);
}

} /* namespace media */
} /* namespace serenegiant */
