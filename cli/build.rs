// Precondition check: quaere-cli embeds skills/ at compile time via
// include_dir!("$CARGO_MANIFEST_DIR/skills"). The repo ships cli/skills/
// as a symlink to ../skills so the crate carries its own path to the
// skill set; cargo package follows the symlink and bakes the contents
// into the published tarball as a regular directory. Surfacing the
// precondition here gives a clearer failure mode than the opaque
// proc-macro error you would get if the directory were missing.

use std::path::PathBuf;

fn main() {
    let manifest_dir =
        std::env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR is set by cargo");
    let skills = PathBuf::from(&manifest_dir).join("skills");

    if !skills.is_dir() {
        panic!(
            "quaere-cli expects the Quaere skill set at {} but it was not found. \
             In the source repo, cli/skills is a symlink to ../skills; in the \
             crates.io tarball, cli/skills is a real directory baked at publish \
             time. If you intentionally relocated the skill set, update the \
             include_dir! path in src/commands/install.rs and this build.rs.",
            skills.display()
        );
    }

    // Trigger a rebuild whenever any embedded skill file changes so that
    // include_dir picks the new content up. Without this directive cargo
    // would only rebuild when src/ changes.
    println!("cargo:rerun-if-changed=skills");
    println!("cargo:rerun-if-changed=build.rs");
}
