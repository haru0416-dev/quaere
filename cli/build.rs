// Precondition check: quaere-cli embeds skills/ at compile time via
// include_dir!("$CARGO_MANIFEST_DIR/../skills"). If that directory is
// missing the include_dir macro would still fail, but with an opaque
// proc-macro error pointing at the macro site rather than at the missing
// directory. Surfacing the precondition here gives a clearer failure mode
// and a louder signal when the cli/ crate has been moved out of the
// Quaere repo layout.

use std::path::PathBuf;

fn main() {
    let manifest_dir =
        std::env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR is set by cargo");
    let skills = PathBuf::from(&manifest_dir).join("..").join("skills");

    if !skills.is_dir() {
        panic!(
            "quaere-cli expects the Quaere skill set at {} but it was not found. \
             This crate must remain inside the Quaere repo layout (cli/ as a \
             subdirectory next to skills/). If you have intentionally relocated \
             cli/, update the include_dir! path in src/commands/install.rs and \
             this build.rs to point at the new skills directory.",
            skills.display()
        );
    }

    // Trigger a rebuild whenever any embedded skill file changes so that
    // include_dir picks the new content up. Without this directive cargo
    // would only rebuild when src/ changes.
    println!("cargo:rerun-if-changed=../skills");
    println!("cargo:rerun-if-changed=build.rs");
}
