/*
 * h264_utils.cpp
 *
 *  Created on: 2017/03/09
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

namespace serenegiant {
namespace media {

/**
 * search AnnexB start marker (N[00] 00 00 01, N>=0)
 * 0: found, otherwise return -1
 * if payload is not null, set next position after annexB start marker (usually nal header)
 * even if this found start marker but has no payload, this return -1
 */
int find_annexb(const uint8_t *data, const size_t &size, const uint8_t **payload) {
	ENTER();

	if (payload) {
		*payload = NULL;
	}
	for (size_t i = 0; i < size - 4; i++) {	// to ignore null payload, use len-4 instead of len-3
		// at least two 0x00 needs
		if ((data[0] != 0x00) || (data[1] != 0x00)) {
			data++;
			continue;
		}
		// if third byte is 0x01, return ok
		if (data[2] == 0x01) {
			if (payload) {
				*payload = data + 3;
			}
			RETURN(0, int);
		}
		data++;
	}

	RETURN(-1, int);
}

nal_unit_type_t get_first_nal_type_annexb(const uint8_t *data, const size_t &size) {

	ENTER();

	nal_unit_type_t result = NAL_UNIT_UNSPECIFIED;
	const uint8_t *payload = NULL;
	int r = find_annexb(data, size, &payload);
	if (!r) {
		result = (nal_unit_type_t)(payload[0] & 0x1f);
	}

	RETURN(result, nal_unit_type_t);
}

/**
 * get vop type of first nal unit
 * @return negative: err, 0: I-frame, 1: P-frame, 2: B-frame, 3: S-frame
 */
int get_first_vop_type_annexb(const uint8_t *data, const size_t &size) {
	ENTER();

	int result = -1;

	if (LIKELY(size > 3)) {
		const uint8_t *payload = NULL;
		const int r = find_annexb(data, size, &payload);
		if (!r) {
			switch (payload[0]) {
			case 0x01:	result = 2; break;	// B-frame
			case 0x61:	result = 1; break;	// P-frame
			case 0x65:	result = 0; break;	// I-frame
			case 0x69:	result = 0; break;	// AUD frame
			case 0xb6: {
				if (payload + 1 < data + size) {
					result = (payload[1] & 0xc0) >> 6;
				}
				break;
			}
			}
		}
	}

	RETURN(result, int);
}

/**
 * get first found vop type, sps, pps and aud will be skipped
 * @return negative: err, 0: I-frame, 1: P-frame, 2: B-frame, 3: S-frame
 */
int get_vop_type_annexb(const uint8_t *_data, const size_t &size) {
	ENTER();

	int result = -1;
	if (LIKELY(size > 3)) {
		const uint8_t *data = _data;
		const uint8_t *payload = NULL;
		int sz = size;
		int ret = find_annexb(data, sz, &payload);
		if (!ret) {
			int ix = payload - data;
			sz -= ix;
			for (uint32_t i = ix; i < size; i++) {
				switch (payload[0]) {
				case 0x01:	result = 2; goto end;	// B-frame
				case 0x61:	result = 1; goto end;	// P-frame
				case 0x65:	result = 0; goto end;	// I-frame
				case 0x69:	result = 0; goto end;	// AUD frame
				case 0xb6: {
					if (payload + 1 < data + size) {
						result = (payload[1] & 0xc0) >> 6;
						goto end;
					}
					break;
				}
				}
//				LOGV("not a I/B/P/S frame, try to found next nal unit");
				ret = find_annexb(&payload[1], sz - 1, &payload);
				if (LIKELY(!ret)) {
					i = payload - data;
					sz = size - i;
				} else {
					goto end;
				}
			}
		}
	}

end:
	RETURN(result, int);
}

/**
 * check whether the frame is key frame
 * @return true is key frame, otherwise return false
 * */
const bool is_iframe(const uint8_t *_data, const size_t &size) {
	ENTER();

	bool result = false;

	if (LIKELY(size > 3)) {
		const uint8_t *data = _data;
		const uint8_t *payload = NULL;
		int sz = size;
		LOGD("find annexB marker");
		int ret = find_annexb(data, sz, &payload);
		if (LIKELY(!ret)) {
			LOGV("found annexB marker");
			bool sps = false, pps = false;
			int ix = payload - data;
			sz -= ix;
			for (uint32_t i = ix; i < size; i++) {
				const nal_unit_type_t type = (nal_unit_type_t)(payload[0] & 0x1f);
				switch (type) {
				case NAL_UNIT_CODEC_SLICE_IDR:
					LOGD("IDR frame");
//					LOGD("SPS/PPS?:%s", bin2hex(&payload[0], 128).c_str());
					result = true;
					goto ret;
//					break;
				case NAL_UNIT_SEQUENCE_PARAM_SET:
				{
					LOGD("found SPS...try to find next annexb marker");
//					LOGI("SPS:%s", bin2hex(&payload[0], 128).c_str());
					sps = true;
					ret = find_annexb(&payload[1], sz - 1, &payload);
					if (LIKELY(!ret)) {
						i = payload - data;
						sz = size - i;
					} else {
						goto end;
					}
					break;
				}
				case NAL_UNIT_PICTURE_PARAM_SET:
				{
					if (LIKELY(sps)) {
						LOGD("found PPS...try to find next annexb marker");
//						LOGI("PPS:%s", bin2hex(&payload[0], 128).c_str());
						pps = true;
						ret = find_annexb(&payload[1], sz  -1, &payload);
						if (LIKELY(!ret)) {
							i = payload - data;
							sz = size - i;
						} else {
							goto end;
						}
					}
					break;
				}
				case NAL_UNIT_PICTURE_DELIMITER:
				{
					LOGD("IDR");
					result = true;
					goto ret;
				}
				case NAL_UNIT_UNSPECIFIED:
				{
					ret = find_annexb(&payload[1], sz  -1, &payload);
					if (LIKELY(!ret)) {
						i = payload - data;
						sz = size - i;
					} else {
						goto end;
					}
					break;
				}
				default:
					// found something start with AnnexB marker
					LOGV("type=%x", type);
					result = sps && pps;
					goto end;
				} // end of switch (type)
			} // end of for
end:
			result = sps && pps;
		} else {
			LOGD("no annexB start marker found");
		}
	} else {
		LOGW("too short");
	}
ret:
	RETURN(result, bool);
}

}	// namespace media
}	// namespace serenegiant
