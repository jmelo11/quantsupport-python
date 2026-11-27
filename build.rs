use std::{env, fs, path::PathBuf};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let root = PathBuf::from(env::var("CARGO_MANIFEST_DIR")?);
    let output = PathBuf::from(env::var("OUT_DIR")?);
    for filename in ["_error_support.py", "_maker_support.py"] {
        let source = root.join("python/quantsupport").join(filename);
        println!("cargo:rerun-if-changed={}", source.display());
        fs::copy(source, output.join(filename))?;
    }
    Ok(())
}
