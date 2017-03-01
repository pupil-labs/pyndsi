/*
 * sensor_uvc.h
 *
 *  Created on: 2017/02/17
 *      Author: saki
 */

#ifndef SENSOR_UVC_H_
#define SENSOR_UVC_H_

#include <vector>
#include <iostream>
#include <fstream>

#include "sensor.h"
#include "h264_decoder.h"

namespace serenegiant {
namespace sensor {

typedef enum nal_unit_type {
	NAL_UNIT_UNSPECIFIED = 0,
	NAL_UNIT_CODEC_SLICE = 1,			// Coded slice of a non-IDR picture == PFrame for AVC
	NAL_UNIT_CODEC_SLICE_A = 2,			// Coded slice data partition A
	NAL_UNIT_CODEC_SLICE_B = 3,			// Coded slice data partition B
	NAL_UNIT_CODEC_SLICE_C = 4,			// Coded slice data partition C
	NAL_UNIT_CODEC_SLICE_IDR = 5,		// Coded slice of an IDR picture == IFrame for AVC
	NAL_UNIT_SEI = 6,					// supplemental enhancement information
	NAL_UNIT_SEQUENCE_PARAM_SET = 7,	// Sequence parameter set == SPS for AVC
	NAL_UNIT_PICTURE_PARAM_SET = 8,		// Picture parameter set == PPS for AVC
	NAL_UNIT_PICTURE_DELIMITER = 9,		// access unit delimiter (AUD)
	NAL_UNIT_END_OF_SEQUENCE = 10,		// End of sequence
	NAL_UNIT_END_OF_STREAM = 11,		// End of stream
	NAL_UNIT_FILLER = 12,				// Filler data
	NAL_UNIT_RESERVED_13 = 13,			// Sequence parameter set extension
	NAL_UNIT_RESERVED_14 = 14,			// Prefix NAL unit
	NAL_UNIT_RESERVED_15 = 15,			// Subset sequence parameter set
	NAL_UNIT_RESERVED_16 = 16,
	NAL_UNIT_RESERVED_17 = 17,
	NAL_UNIT_RESERVED_18 = 18,
	NAL_UNIT_RESERVED_19 = 19,			// Coded slice of an auxiliary coded picture without partitioning
	NAL_UNIT_RESERVED_20 = 20,			// Coded slice extension
	NAL_UNIT_RESERVED_21 = 21,			// Coded slice extension for depth view components
	NAL_UNIT_RESERVED_22 = 22,
	NAL_UNIT_RESERVED_23 = 23,
	NAL_UNIT_UNSPECIFIED_24 = 24,
	NAL_UNIT_UNSPECIFIED_25 = 25,
	NAL_UNIT_UNSPECIFIED_26 = 26,
	NAL_UNIT_UNSPECIFIED_27 = 27,
	NAL_UNIT_UNSPECIFIED_28 = 28,
	NAL_UNIT_UNSPECIFIED_29 = 29,
	NAL_UNIT_UNSPECIFIED_30 = 30,
	NAL_UNIT_UNSPECIFIED_31 = 31,
} nal_unit_type_t;

class UVCSensor: public virtual Sensor {
private:
	media::H264Decoder *h264;
	std::vector<uint8_t> h264_output;
	uint32_t h264_width, h264_height;
	bool need_wait_iframe;
	uint32_t last_sequence;
	std::ofstream ofs;
	uint32_t received_frames;
	uint32_t error_frames;
	uint32_t skipped_frames;
	size_t received_bytes;
	nsecs_t start_time;
protected:
	virtual int handle_notify_update(const std::string &identity, const std::string &payload);
	virtual int handle_frame_data(const std::string &identity,
		const publish_header_t &header, const size_t &size, const uint8_t *data);
	int handle_frame_data_mjpeg(const uint32_t &width, const uint32_t &height,
		const size_t &size, const uint8_t *data, const int64_t &presentation_time_us);
	int handle_frame_data_h264(const uint32_t &width, const uint32_t &height,
		const size_t &size, const uint8_t *data, const int64_t &presentation_time_us);
	int handle_frame_data_vp8(const uint32_t &width, const uint32_t &height,
		const size_t &size, const uint8_t *data, const int64_t &presentation_time_us);
	const bool is_iframe(const size_t &size, const uint8_t *data);
public:
	UVCSensor(const char *uuid, const char *name);
	virtual ~UVCSensor();
	virtual int start(const char *command, const char *notify, const char *data);
};

} /* namespace sensor */
} /* namespace serenegiant */

#endif /* SENSOR_UVC_H_ */
