use std::fs::{self, File};
use std::io::{self, Read};
use std::path::{Path, PathBuf};
use sha2::{Sha256, Digest};
use tar::Archive;
use crate::manifest::{Manifest, ManifestError};

pub struct ArtifactStore {
    base_dir: PathBuf,
}

impl ArtifactStore {
    pub fn new(base_dir: impl AsRef<Path>) -> Self {
        Self {
            base_dir: base_dir.as_ref().to_path_buf(),
        }
    }

    /// Extract a .pkg file to the store, performing the strict manifest check and checksum validation.
    /// Returns the parsed and validated Manifest if successful.
    pub fn install_package(&self, pkg_path: impl AsRef<Path>) -> Result<Manifest, ManifestError> {
        let pkg_file = File::open(pkg_path)?;
        let mut archive = Archive::new(pkg_file);

        // Ensure temporary extraction directory exists
        let tmp_dir = self.base_dir.join("tmp_install");
        if tmp_dir.exists() {
            fs::remove_dir_all(&tmp_dir)?;
        }
        fs::create_dir_all(&tmp_dir)?;

        // Extract files
        archive.unpack(&tmp_dir)?;

        // Read and parse manifest
        let manifest_path = tmp_dir.join("manifest.json");
        if !manifest_path.exists() {
            fs::remove_dir_all(&tmp_dir)?;
            return Err(ManifestError::MissingFile("manifest.json".to_string()));
        }

        let manifest_file = File::open(&manifest_path)?;
        let manifest: Manifest = serde_json::from_reader(manifest_file)?;

        // Perform strict compatibility validation
        if let Err(e) = manifest.validate_compatibility() {
            fs::remove_dir_all(&tmp_dir)?;
            return Err(e);
        }

        // Verify checksums of all files listed in the manifest
        for (pkg_filename, expected_hash) in &manifest.files {
            // Map the package's internal filename to extracted path
            let file_path = tmp_dir.join(pkg_filename);
            if !file_path.exists() {
                fs::remove_dir_all(&tmp_dir)?;
                return Err(ManifestError::MissingFile(pkg_filename.clone()));
            }

            let computed = match self.compute_sha256(&file_path) {
                Ok(hash) => hash,
                Err(e) => {
                    fs::remove_dir_all(&tmp_dir)?;
                    return Err(ManifestError::Io(e));
                }
            };

            if computed != *expected_hash {
                fs::remove_dir_all(&tmp_dir)?;
                return Err(ManifestError::ChecksumMismatch {
                    file: pkg_filename.clone(),
                    expected: expected_hash.clone(),
                    actual: computed,
                });
            }
        }

        // Atomically replace target directory contents
        let active_dir = self.base_dir.join("active");
        if active_dir.exists() {
            fs::remove_dir_all(&active_dir)?;
        }
        fs::create_dir_all(&active_dir)?;

        // Copy verified files to active folder
        for entry in fs::read_dir(&tmp_dir)? {
            let entry = entry?;
            let dest_path = active_dir.join(entry.file_name());
            fs::rename(entry.path(), dest_path)?;
        }

        // Clean up tmp_dir
        fs::remove_dir_all(&tmp_dir)?;

        Ok(manifest)
    }

    /// Retrieve the path of an active file in the store
    pub fn get_active_file(&self, filename: &str) -> PathBuf {
        self.base_dir.join("active").join(filename)
    }

    fn compute_sha256(&self, path: &Path) -> io::Result<String> {
        let mut file = File::open(path)?;
        let mut hasher = Sha256::new();
        let mut buffer = [0; 4096];
        loop {
            let count = file.read(&mut buffer)?;
            if count == 0 {
                break;
            }
            hasher.update(&buffer[..count]);
        }
        Ok(hex::encode(hasher.finalize()))
    }
}
