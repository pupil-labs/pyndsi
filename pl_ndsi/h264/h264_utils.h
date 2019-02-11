/*
 * h264_utils.h
 *
 *  Created on: 2017/03/09
 *      Author: saki
 */

#ifndef MEDIA_H264_UTILS_H_
#define MEDIA_H264_UTILS_H_

#include <stdint.h>

namespace serenegiant {
namespace media {

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

int find_annexb(const uint8_t *data, const size_t &len, const uint8_t **payload);
nal_unit_type_t get_first_nal_type_annexb(const uint8_t *data, const size_t &len);
/**
 * get vop type of first nal unit
 * @return negative: err, 0: I-frame, 1: P-frame, 2: B-frame, 3: S-frame
 */
int get_first_vop_type_annexb(const uint8_t *data, const size_t &size);
/**
 * @return negative: err, 0: I-frame, 1: P-frame, 2: B-frame, 3: S-frame
 */
int get_vop_type_annexb(const uint8_t *data, const size_t &size);
const bool is_iframe(const uint8_t *data, const size_t &size);

}	// namespace media
}	// namespace serenegiant

#endif /* MEDIA_H264_UTILS_H_ */
