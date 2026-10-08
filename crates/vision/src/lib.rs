use bytes::{Bytes, BytesMut};

pub struct MjpegFrameExtractor {
    buffer: BytesMut,
}

impl MjpegFrameExtractor {
    pub fn new() -> Self {
        Self {
            buffer: BytesMut::with_capacity(64 * 1024),
        }
    }

    pub fn push_chunk(&mut self, chunk: &[u8]) -> Option<Bytes> {
        self.buffer.extend_from_slice(chunk);
        self.extract_frame()
    }

    pub fn extract_frame(&mut self) -> Option<Bytes> {
        let buf = &self.buffer[..];
        let soi = buf.windows(2).position(|w| w == [0xFF, 0xD8])?;
        let eoi_rel = buf[soi..].windows(2).position(|w| w == [0xFF, 0xD9])?;
        let eoi = soi + eoi_rel + 2;

        let frame_bytes = self.buffer.split_to(eoi).freeze();
        if soi > 0 {
            Some(frame_bytes.slice(soi..))
        } else {
            Some(frame_bytes)
        }
    }
}

impl Default for MjpegFrameExtractor {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_mjpeg_frame() {
        let mut extractor = MjpegFrameExtractor::new();
        let sample = vec![
            0x00, 0x11, // junk prefix
            0xFF, 0xD8, // SOI
            0x12, 0x34, 0x56,
            0xFF, 0xD9, // EOI
            0xAA, 0xBB, // trailing bytes for next frame
        ];
        let frame = extractor.push_chunk(&sample).expect("Frame should extract");
        assert_eq!(&frame[..], &[0xFF, 0xD8, 0x12, 0x34, 0x56, 0xFF, 0xD9]);
    }
}
