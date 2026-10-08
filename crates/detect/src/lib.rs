use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use store::DetectionEvent;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct BoundingBox {
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DetectionItem {
    pub class_name: String,
    pub confidence: f32,
    pub bbox: BoundingBox,
}

pub struct DebounceFilter {
    min_persistence_frames: u32,
    active_tracks: HashMap<String, TrackedItem>,
}

struct TrackedItem {
    first_seen: String,
    last_seen: String,
    frame_count: u32,
    best_conf: f32,
    emitted: bool,
}

impl DebounceFilter {
    pub fn new(min_persistence_frames: u32) -> Self {
        Self {
            min_persistence_frames,
            active_tracks: HashMap::new(),
        }
    }

    pub fn update(&mut self, items: &[DetectionItem]) -> Vec<DetectionEvent> {
        let now = Utc::now().to_rfc3339();
        let mut events = Vec::new();
        let mut present_classes = HashMap::new();

        for item in items {
            let entry = present_classes.entry(item.class_name.clone()).or_insert((0u32, item.confidence));
            entry.0 += 1;
            if item.confidence > entry.1 {
                entry.1 = item.confidence;
            }
        }

        for (cls, (_count, conf)) in &present_classes {
            let track = self.active_tracks.entry(cls.clone()).or_insert_with(|| TrackedItem {
                first_seen: now.clone(),
                last_seen: now.clone(),
                frame_count: 0,
                best_conf: *conf,
                emitted: false,
            });

            track.last_seen = now.clone();
            track.frame_count += 1;
            if *conf > track.best_conf {
                track.best_conf = *conf;
            }

            if track.frame_count >= self.min_persistence_frames && !track.emitted {
                track.emitted = true;
                events.push(DetectionEvent {
                    ts: now.clone(),
                    cls: cls.clone(),
                    conf: track.best_conf,
                    frames: track.frame_count,
                    first: track.first_seen.clone(),
                    last: track.last_seen.clone(),
                    zone: "center".to_string(),
                });
            }
        }

        self.active_tracks.retain(|cls, _| present_classes.contains_key(cls));
        events
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_debounce_filter() {
        let mut filter = DebounceFilter::new(3);
        let item = DetectionItem {
            class_name: "person".to_string(),
            confidence: 0.9,
            bbox: BoundingBox { x: 0.1, y: 0.1, width: 0.5, height: 0.5 },
        };

        // Frame 1
        assert!(filter.update(&[item.clone()]).is_empty());
        // Frame 2
        assert!(filter.update(&[item.clone()]).is_empty());
        // Frame 3 -> Should emit event
        let events = filter.update(&[item.clone()]);
        assert_eq!(events.len(), 1);
        assert_eq!(events[0].cls, "person");

        // Frame 4 -> Already emitted, no duplicate
        assert!(filter.update(&[item.clone()]).is_empty());
    }
}
