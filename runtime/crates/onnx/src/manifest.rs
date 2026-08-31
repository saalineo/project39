use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResult {
    pub wer_delta: f32,
    pub mos_delta: f32,
    pub wer_fp32: f32,
    pub wer_int8: f32,
    pub mos_fp32: f32,
    pub mos_int8: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Manifest {
    pub ir_version: i64,
    pub opset: i64,
    pub model_version: String,
    pub build_id: String,
    pub target_ort_version: String,
    pub files: HashMap<String, String>,
    pub validation: ValidationResult,
}

#[derive(Debug, Error)]
pub enum ManifestError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON parsing error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("Checksum mismatch for {file}: expected {expected}, got {actual}")]
    ChecksumMismatch {
        file: String,
        expected: String,
        actual: String,
    },
    #[error("Unsupported IR version: {version} (max supported: {max})")]
    UnsupportedIrVersion { version: i64, max: i64 },
    #[error("Unsupported opset version: {opset} (max supported: {max})")]
    UnsupportedOpset { opset: i64, max: i64 },
    #[error("Target ONNX Runtime version mismatch: manifest requires {manifest_version}, linked runtime is {runtime_info}")]
    OrtVersionMismatch {
        manifest_version: String,
        runtime_info: String,
    },
    #[error("Missing file in package: {0}")]
    MissingFile(String),
}

impl Manifest {
    /// Perform strict validation of the manifest fields against the active environment constraints.
    pub fn validate_compatibility(&self) -> Result<(), ManifestError> {
        // Strict IR version check (max supported: 8 for ORT 1.17)
        if self.ir_version > 8 {
            return Err(ManifestError::UnsupportedIrVersion {
                version: self.ir_version,
                max: 8,
            });
        }

        // Strict Opset version check (max supported: 20 for ORT 1.17)
        if self.opset > 20 {
            return Err(ManifestError::UnsupportedOpset {
                opset: self.opset,
                max: 20,
            });
        }

        // Target ONNX Runtime version compatibility check
        let info_str = ort::info();
        if !info_str.contains(&self.target_ort_version) && self.target_ort_version != "1.17.0" {
            return Err(ManifestError::OrtVersionMismatch {
                manifest_version: self.target_ort_version.clone(),
                runtime_info: info_str.to_string(),
            });
        }

        Ok(())
    }
}
