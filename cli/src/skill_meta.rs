use anyhow::{Context, Result};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

pub const MAX_SKILL_LINES: usize = 500;
pub const REQUIRED_FIELDS: &[&str] = &["name", "description", "compatibility", "license"];

#[derive(Debug, Default)]
pub struct SkillReport {
    pub issues: Vec<String>,
}

impl SkillReport {
    pub fn is_clean(&self) -> bool {
        self.issues.is_empty()
    }
}

/// Inspect a single skill directory and return any structural issues found.
pub fn check_skill(skill_dir: &Path) -> Result<SkillReport> {
    let skill_name = skill_dir
        .file_name()
        .and_then(|n| n.to_str())
        .context("skill dir has no file name")?
        .to_owned();

    let mut issues = Vec::new();
    let skill_md = skill_dir.join("SKILL.md");
    if !skill_md.is_file() {
        issues.push("missing SKILL.md".to_owned());
        return Ok(SkillReport { issues });
    }

    let text =
        fs::read_to_string(&skill_md).with_context(|| format!("reading {}", skill_md.display()))?;
    let line_count = text.lines().count();
    if line_count > MAX_SKILL_LINES {
        issues.push(format!(
            "{} lines exceeds {}-line budget",
            line_count, MAX_SKILL_LINES
        ));
    }

    let frontmatter = parse_frontmatter(&text, &mut issues);

    for required in REQUIRED_FIELDS {
        if !frontmatter.contains_key(*required) {
            issues.push(format!("missing frontmatter field `{}`", required));
        }
    }

    if let Some(name) = frontmatter.get("name") {
        if name != &skill_name {
            issues.push(format!(
                "name `{}` does not match directory `{}`",
                name, skill_name
            ));
        }
        if !is_kebab_case(name) {
            issues.push(format!("name `{}` is not kebab-case", name));
        }
    }

    if let Some(description) = frontmatter.get("description") {
        if !description.starts_with("This skill should be used") {
            issues.push("description should start with `This skill should be used`".to_owned());
        }
        if description.len() < 80 {
            issues.push("description is too short (< 80 chars)".to_owned());
        }
    }

    if let Some(license) = frontmatter.get("license") {
        if license != "MIT" {
            issues.push(format!("license `{}` is not MIT", license));
        }
    }

    let _ = skill_name; // name is already known to the caller from the directory path
    Ok(SkillReport { issues })
}

fn parse_frontmatter(text: &str, issues: &mut Vec<String>) -> HashMap<String, String> {
    let mut lines = text.lines();
    match lines.next() {
        Some(line) if line.trim() == "---" => {}
        _ => {
            issues.push("missing opening frontmatter delimiter".to_owned());
            return HashMap::new();
        }
    }

    let mut fm = HashMap::new();
    for line in lines {
        if line.trim() == "---" {
            return fm;
        }
        if line.trim().is_empty() {
            continue;
        }
        let Some((key, value)) = line.split_once(':') else {
            issues.push(format!("frontmatter line missing `:` -> `{}`", line));
            continue;
        };
        let key = key.trim().to_owned();
        let raw = value.trim();
        let is_quoted = (raw.starts_with('"') && raw.ends_with('"'))
            || (raw.starts_with('\'') && raw.ends_with('\''));
        if raw.contains(": ") && !is_quoted {
            issues.push(format!(
                "frontmatter value containing ': ' must be quoted: `{}`",
                raw
            ));
        }
        let value = raw.trim_matches(|c| c == '"' || c == '\'').to_owned();
        fm.insert(key, value);
    }
    issues.push("missing closing frontmatter delimiter".to_owned());
    fm
}

fn is_kebab_case(name: &str) -> bool {
    if name.is_empty() {
        return false;
    }
    let mut last_was_dash = false;
    for (i, ch) in name.chars().enumerate() {
        if ch == '-' {
            if i == 0 || last_was_dash {
                return false;
            }
            last_was_dash = true;
            continue;
        }
        if !ch.is_ascii_lowercase() && !ch.is_ascii_digit() {
            return false;
        }
        last_was_dash = false;
    }
    !last_was_dash
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn kebab_case_accepts_valid_names() {
        assert!(is_kebab_case("quaere-semantic"));
        assert!(is_kebab_case("a-b-c"));
        assert!(is_kebab_case("a1-b2"));
        assert!(is_kebab_case("solo"));
    }

    #[test]
    fn kebab_case_rejects_invalid_names() {
        assert!(!is_kebab_case(""));
        assert!(!is_kebab_case("-leading"));
        assert!(!is_kebab_case("trailing-"));
        assert!(!is_kebab_case("double--dash"));
        assert!(!is_kebab_case("UpperCase"));
        assert!(!is_kebab_case("under_score"));
    }

    #[test]
    fn parse_frontmatter_happy_path() {
        let mut issues = Vec::new();
        let fm = parse_frontmatter("---\nname: foo\ndescription: hi\n---\nbody\n", &mut issues);
        assert_eq!(fm.get("name").map(String::as_str), Some("foo"));
        assert_eq!(fm.get("description").map(String::as_str), Some("hi"));
        assert!(issues.is_empty());
    }

    #[test]
    fn parse_frontmatter_detects_missing_open() {
        let mut issues = Vec::new();
        parse_frontmatter("name: foo\n---\n", &mut issues);
        assert!(issues
            .iter()
            .any(|e| e.contains("opening frontmatter delimiter")));
    }

    #[test]
    fn parse_frontmatter_detects_missing_close() {
        let mut issues = Vec::new();
        parse_frontmatter("---\nname: foo\n", &mut issues);
        assert!(issues
            .iter()
            .any(|e| e.contains("closing frontmatter delimiter")));
    }
}
