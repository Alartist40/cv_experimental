use axum::{
    extract::{Query, State},
    http::header,
    response::{IntoResponse, Json, Response},
    routing::{get, post},
    Router,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use std::process::Stdio;
use std::sync::Arc;
use store::{DetectionEvent, DetectionStore};
use tokio::process::Command;
use tower_http::services::ServeDir;

#[derive(Clone)]
struct AppState {
    store: Arc<DetectionStore>,
    ollama_url: String,
    ollama_model: String,
}

#[derive(Deserialize)]
struct AskRequest {
    prompt: String,
    date: Option<String>,
}

#[derive(Serialize)]
struct AskResponse {
    response: String,
}

#[derive(Deserialize)]
struct EventsQuery {
    date: Option<String>,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    // Spawn YOLO detection background process automatically
    println!(">>> Launching unified YOLO Vision Engine...");
    let python_bin = ".venv/bin/python3";
    let script = "crates/detect_service.py";
    
    let mut detect_child = Command::new(python_bin)
        .arg(script)
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .spawn()?;

    // Ensure detector terminates when hubd stops
    tokio::spawn(async move {
        let _ = detect_child.wait().await;
    });

    let store = Arc::new(DetectionStore::new("data/detections"));
    let state = AppState {
        store,
        ollama_url: std::env::var("OLLAMA_URL").unwrap_or_else(|_| "http://127.0.0.1:11434".to_string()),
        ollama_model: std::env::var("OLLAMA_MODEL").unwrap_or_else(|_| "qwen2.5:3b-instruct".to_string()),
    };

    let app = Router::new()
        .route("/frame.jpg", get(live_frame_handler))
        .route("/api/live_detections", get(live_detections_handler))
        .route("/api/events", get(get_events_handler))
        .route("/api/ask", post(ask_handler))
        .route("/api/face/scan", post(face_scan_handler))
        .route("/api/face/enroll", post(face_enroll_handler))
        .route("/api/face/list", get(face_list_handler))
        .route("/api/face/delete", post(face_delete_handler))
        .route("/api/gesture/toggle", post(gesture_toggle_handler))
        .route("/api/gesture/status", get(gesture_status_handler))
        .route("/api/mode", get(mode_get_handler).post(mode_set_handler))
        .route("/api/filter", get(filter_get_handler).post(filter_set_handler))
        .nest_service("/", ServeDir::new("ui"))
        .with_state(state);

    let port: u16 = std::env::var("PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8085);
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    println!(">>> Vision Hub unified service running at http://localhost:{}", port);

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
}

async fn live_frame_handler() -> Response {
    match tokio::fs::read("data/live_frame.jpg").await {
        Ok(bytes) => Response::builder()
            .header(header::CONTENT_TYPE, "image/jpeg")
            .header(header::CACHE_CONTROL, "no-cache, no-store, must-revalidate")
            .header("Access-Control-Allow-Origin", "*")
            .body(axum::body::Body::from(bytes))
            .unwrap(),
        Err(_) => Response::builder()
            .status(404)
            .body(axum::body::Body::from("No frame available"))
            .unwrap(),
    }
}

async fn live_detections_handler() -> Response {
    let content = tokio::fs::read_to_string("data/live_detections.json").await.unwrap_or_else(|_| "[]".to_string());
    Response::builder()
        .header(header::CONTENT_TYPE, "application/json")
        .header(header::CACHE_CONTROL, "no-cache")
        .header("Access-Control-Allow-Origin", "*")
        .body(axum::body::Body::from(content))
        .unwrap()
}

async fn get_events_handler(
    State(state): State<AppState>,
    Query(query): Query<EventsQuery>,
) -> Json<Vec<DetectionEvent>> {
    let date = query.date.unwrap_or_else(|| Utc::now().format("%Y-%m-%d").to_string());
    let events = state.store.read_day_events(&date).await.unwrap_or_default();
    Json(events)
}

async fn ask_handler(
    State(state): State<AppState>,
    Json(payload): Json<AskRequest>,
) -> impl IntoResponse {
    let date = payload.date.unwrap_or_else(|| Utc::now().format("%Y-%m-%d").to_string());
    let events = state.store.read_day_events(&date).await.unwrap_or_default();
    let summary = DetectionStore::summarize_for_slm(&events);

    let system_prompt = format!(
        "You are Vision Hub SLM. Answer user questions based strictly on this detection summary:\n{}",
        summary
    );

    let client = reqwest::Client::new();
    let ollama_req = serde_json::json!({
        "model": state.ollama_model,
        "prompt": format!("{}\n\nUser Question: {}", system_prompt, payload.prompt),
        "stream": false,
        "keep_alive": 0
    });

    let resp_res = client
        .post(format!("{}/api/generate", state.ollama_url))
        .json(&ollama_req)
        .send()
        .await;

    match resp_res {
        Ok(res) if res.status().is_success() => {
            if let Ok(body) = res.json::<serde_json::Value>().await {
                let answer = body["response"].as_str().unwrap_or("No response generated").to_string();
                return Json(AskResponse { response: answer });
            }
        }
        _ => {}
    }

    Json(AskResponse {
        response: format!(
            "[Ollama dormant/unreachable] Daily summary for {}:\n{}",
            date, summary
        ),
    })
}

#[derive(Deserialize)]
struct FaceEnrollRequest {
    name: String,
    role: Option<String>,
    clearance: Option<String>,
}

#[derive(Deserialize)]
struct FaceDeleteRequest {
    name: String,
}

async fn run_face_cli(args: &[&str]) -> String {
    let python_bin = ".venv/bin/python3";
    let script = "crates/face_service.py";
    let mut cmd = Command::new(python_bin);
    cmd.arg(script);
    for arg in args {
        cmd.arg(arg);
    }
    match cmd.output().await {
        Ok(out) => {
            let stdout = String::from_utf8_lossy(&out.stdout);
            for line in stdout.lines().rev() {
                let trimmed = line.trim();
                if trimmed.starts_with('{') && trimmed.ends_with('}') {
                    return trimmed.to_string();
                }
            }
            stdout.to_string()
        }
        Err(e) => serde_json::json!({"status": "error", "message": e.to_string()}).to_string(),
    }
}

async fn face_scan_handler() -> Response {
    let output = run_face_cli(&["scan"]).await;
    Response::builder()
        .header(header::CONTENT_TYPE, "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .body(axum::body::Body::from(output))
        .unwrap()
}

async fn face_enroll_handler(Json(payload): Json<FaceEnrollRequest>) -> Response {
    let role = payload.role.unwrap_or_else(|| "OPERATOR".to_string());
    let clearance = payload.clearance.unwrap_or_else(|| "LEVEL-5".to_string());
    let output = run_face_cli(&["enroll", &payload.name, &role, &clearance]).await;
    Response::builder()
        .header(header::CONTENT_TYPE, "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .body(axum::body::Body::from(output))
        .unwrap()
}

async fn face_list_handler() -> Response {
    let output = run_face_cli(&["list"]).await;
    Response::builder()
        .header(header::CONTENT_TYPE, "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .body(axum::body::Body::from(output))
        .unwrap()
}

async fn face_delete_handler(Json(payload): Json<FaceDeleteRequest>) -> Response {
    let output = run_face_cli(&["delete", &payload.name]).await;
    Response::builder()
        .header(header::CONTENT_TYPE, "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .body(axum::body::Body::from(output))
        .unwrap()
}

async fn gesture_toggle_handler() -> Response {
    let flag_path = "data/gesture_armed.flag";
    let is_armed = tokio::fs::try_exists(flag_path).await.unwrap_or(false);
    if is_armed {
        let _ = tokio::fs::remove_file(flag_path).await;
        Response::builder()
            .header(header::CONTENT_TYPE, "application/json")
            .header("Access-Control-Allow-Origin", "*")
            .body(axum::body::Body::from("{\"armed\": false, \"message\": \"Hand gesture control DISARMED.\"}"))
            .unwrap()
    } else {
        let _ = tokio::fs::write(flag_path, b"1").await;
        Response::builder()
            .header(header::CONTENT_TYPE, "application/json")
            .header("Access-Control-Allow-Origin", "*")
            .body(axum::body::Body::from("{\"armed\": true, \"message\": \"Hand gesture control ARMED.\"}"))
            .unwrap()
    }
}

async fn gesture_status_handler() -> Response {
    let flag_path = "data/gesture_armed.flag";
    let is_armed = tokio::fs::try_exists(flag_path).await.unwrap_or(false);
    Response::builder()
        .header(header::CONTENT_TYPE, "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .body(axum::body::Body::from(format!("{{\"armed\": {}}}", is_armed)))
        .unwrap()
}

#[derive(Deserialize)]
struct ModeRequest {
    mode: String,
}

async fn mode_get_handler() -> Response {
    let mode = tokio::fs::read_to_string("data/current_mode.txt")
        .await
        .unwrap_or_else(|_| "OBJECT_DETECT".to_string());
    Response::builder()
        .header(header::CONTENT_TYPE, "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .body(axum::body::Body::from(format!("{{\"mode\": \"{}\"}}", mode.trim())))
        .unwrap()
}

async fn mode_set_handler(Json(payload): Json<ModeRequest>) -> Response {
    let mode = payload.mode.trim().to_uppercase();
    let _ = tokio::fs::write("data/current_mode.txt", mode.as_bytes()).await;
    Response::builder()
        .header(header::CONTENT_TYPE, "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .body(axum::body::Body::from(format!("{{\"status\": \"ok\", \"mode\": \"{}\"}}", mode)))
        .unwrap()
}

#[derive(Deserialize)]
struct FilterRequest {
    filter: String,
}

async fn filter_get_handler() -> Response {
    let filter = tokio::fs::read_to_string("data/lighting_filter.txt")
        .await
        .unwrap_or_else(|_| "AUTO".to_string());
    Response::builder()
        .header(header::CONTENT_TYPE, "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .body(axum::body::Body::from(format!("{{\"filter\": \"{}\"}}", filter.trim())))
        .unwrap()
}

async fn filter_set_handler(Json(payload): Json<FilterRequest>) -> Response {
    let filter = payload.filter.trim().to_uppercase();
    let _ = tokio::fs::write("data/lighting_filter.txt", filter.as_bytes()).await;
    Response::builder()
        .header(header::CONTENT_TYPE, "application/json")
        .header("Access-Control-Allow-Origin", "*")
        .body(axum::body::Body::from(format!("{{\"status\": \"ok\", \"filter\": \"{}\"}}", filter)))
        .unwrap()
}




