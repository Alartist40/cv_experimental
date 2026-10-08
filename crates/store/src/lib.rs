use std::collections::HashMap;
use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};
use tokio::fs::{create_dir_all, OpenOptions};
use tokio::io::AsyncWriteExt;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DetectionEvent {
    pub ts: String,
    pub cls: String,
    pub conf: f32,
    pub frames: u32,
    pub first: String,
    pub last: String,
    pub zone: String,
}

pub struct DetectionStore {
    base_dir: PathBuf,
}

impl DetectionStore {
    pub fn new(base_dir: impl AsRef<Path>) -> Self {
        Self {
            base_dir: base_dir.as_ref().to_path_buf(),
        }
    }

    pub fn daily_file_path(&self, date_str: &str) -> PathBuf {
        self.base_dir.join(format!("{}.jsonl", date_str))
    }

    pub async fn append_event(&self, event: &DetectionEvent) -> anyhow::Result<()> {
        create_dir_all(&self.base_dir).await?;
        let date_prefix = if event.ts.len() >= 10 {
            &event.ts[0..10]
        } else {
            "unspecified"
        };
        let file_path = self.daily_file_path(date_prefix);
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(file_path)
            .await?;
        let mut line = serde_json::to_string(event)?;
        line.push('\n');
        file.write_all(line.as_bytes()).await?;
        file.flush().await?;
        Ok(())
    }

    pub async fn read_day_events(&self, date_str: &str) -> anyhow::Result<Vec<DetectionEvent>> {
        let file_path = self.daily_file_path(date_str);
        if !file_path.exists() {
            return Ok(Vec::new());
        }
        let content = tokio::fs::read_to_string(file_path).await?;
        let mut events = Vec::new();
        for line in content.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }
            if let Ok(evt) = serde_json::from_str::<DetectionEvent>(line) {
                events.push(evt);
            }
        }
        Ok(events)
    }

    pub fn summarize_for_slm(events: &[DetectionEvent]) -> String {
        if events.is_empty() {
            return "No detections recorded for this period.".to_string();
        }
        let mut counts: HashMap<String, u32> = HashMap::new();
        let mut first_seen: HashMap<String, String> = HashMap::new();
        let mut last_seen: HashMap<String, String> = HashMap::new();

        for evt in events {
            *counts.entry(evt.cls.clone()).or_default() += 1;
            first_seen.entry(evt.cls.clone()).or_insert_with(|| evt.first.clone());
            last_seen.insert(evt.cls.clone(), evt.last.clone());
        }

        let mut lines = Vec::new();
        lines.push(format!("Total events: {}", events.len()));
        for (cls, count) in counts {
            let f = first_seen.get(&cls).cloned().unwrap_or_default();
            let l = last_seen.get(&cls).cloned().unwrap_or_default();
            lines.push(format!(
                "- Class '{}': {} times (first: {}, last: {})",
                cls, count, f, l
            ));
        }
        lines.join("\n")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_store_and_summarize() {
        let temp_dir = std::env::temp_dir().join("test_store_events");
        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
        let store = DetectionStore::new(&temp_dir);

        let event = DetectionEvent {
            ts: "2026-10-06T14:22:01+09:00".to_string(),
            cls: "person".to_string(),
            conf: 0.87,
            frames: 42,
            first: "14:21:35".to_string(),
            last: "14:22:01".to_string(),
            zone: "center".to_string(),
        };

        store.append_event(&event).await.unwrap();
        let read = store.read_day_events("2026-10-06").await.unwrap();
        assert_eq!(read.len(), 1);
        assert_eq!(read[0].cls, "person");

        let summary = DetectionStore::summarize_for_slm(&read);
        assert!(summary.contains("Class 'person': 1 times"));
        let _ = tokio::fs::remove_dir_all(&temp_dir).await;
    }
}
