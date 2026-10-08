use axum::{
    body::Body,
    http::header,
    response::Response,
    routing::get,
    Router,
};
use std::process::Stdio;
use tokio::process::Command;
use tokio_util::io::ReaderStream;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    let app = Router::new()
        .route("/stream", get(stream_handler));

    let addr = std::net::SocketAddr::from(([0, 0, 0, 0], 8081));
    println!("Webcam proxy running at http://{}", addr);
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
}

async fn stream_handler() -> Response {
    let mut cmd = Command::new("ffmpeg");
    cmd.args(&[
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-video_size", "640x480",
        "-framerate", "15",
        "-i", "/dev/video0",
        "-f", "mpjpeg",
        "-boundary_tag", "123456789000000000000987654321",
        "pipe:1"
    ])
    .stdout(Stdio::piped())
    .stderr(Stdio::null());

    let child = match cmd.spawn() {
        Ok(c) => c,
        Err(_) => return Response::builder().status(500).body(Body::empty()).unwrap(),
    };

    let stdout = child.stdout.unwrap();
    let stream = ReaderStream::new(stdout);
    let body = Body::from_stream(stream);

    Response::builder()
        .header(header::CONTENT_TYPE, "multipart/x-mixed-replace;boundary=123456789000000000000987654321")
        .header("Access-Control-Allow-Origin", "*")
        .body(body)
        .unwrap()
}
