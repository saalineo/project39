use onnx::{ArtifactStore, GraphSession, ManifestError};
use std::path::Path;
use std::time::Instant;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("=== Project39 M1 Test Driver (Day 4) ===");

    // Paths
    let pkg_path = Path::new("../artifacts/model_en.pkg");
    let store_dir = Path::new("./artifact_store_data");

    // Initialize artifact store
    let store = ArtifactStore::new(store_dir);

    // Load valid package
    println!("Loading valid package from {:?}...", pkg_path);
    let start_time = Instant::now();
    let manifest = match store.install_package(pkg_path) {
        Ok(m) => {
            println!("Manifest verification PASSED.");
            println!("  Model Version: {}", m.model_version);
            println!("  Build ID: {}", m.build_id);
            println!("  Opset: {}", m.opset);
            m
        }
        Err(e) => {
            eprintln!("Failed to install valid package: {}", e);
            return Err(e.into());
        }
    };
    println!("Install completed in: {:?}", start_time.elapsed());

    // Load model into GraphSession and run inference
    let model_onnx_path = store.get_active_file("model.onnx");
    println!(
        "Initializing ONNX Runtime Session from {:?}...",
        model_onnx_path
    );
    let session_start = Instant::now();
    let mut session = GraphSession::new(model_onnx_path)?;
    println!("Session initialized in: {:?}", session_start.elapsed());

    // Run one inference pass
    let input_tensor = vec![0.1f32; 128];
    println!("Running inference with synthetic input tensor of length 128...");
    let infer_start = Instant::now();
    let output = session.run(&input_tensor)?;
    let infer_duration = infer_start.elapsed();

    println!("Inference output shape: [{}]", output.len());
    println!("Inference output: {:?}", output);
    println!("Inference completed in: {:?}", infer_duration);

    // Test gate: loading a tampered package fails
    println!("\nTesting validation gate: Loading a tampered package...");
    let tampered_pkg_path = Path::new("./tampered_model.pkg");

    // Create a tampered package by writing random bytes
    std::fs::write(tampered_pkg_path, b"corrupted data package")?;

    match store.install_package(tampered_pkg_path) {
        Ok(_) => {
            panic!("Gate FAILED: Loaded a tampered package successfully!");
        }
        Err(e) => {
            println!(
                "Gate PASSED: Loading tampered package failed with error: {}",
                e
            );
        }
    }

    // Clean up temporary files
    let _ = std::fs::remove_file(tampered_pkg_path);

    println!("\n=== Day 4 Gate Validation Successful ===");
    Ok(())
}
