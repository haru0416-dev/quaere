use anyhow::Result;

pub fn run() -> Result<()> {
    println!("quaere {}", env!("CARGO_PKG_VERSION"));
    Ok(())
}
