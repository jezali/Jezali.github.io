use wasm_bindgen::prelude::*;
use wasm_bindgen_futures::JsFuture;
use web_sys::{Request, RequestInit, RequestMode, Response};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use crate::util::{get_element_by_id, local_storage, now_ms};

const CACHE_KEY: &str = "jezali_repos_cache";
const CACHE_TIME_KEY: &str = "jezali_repos_time";
const ONE_HOUR_MS: f64 = 3600.0 * 1000.0;
const FALLBACK_REPOS_JSON: &str = include_str!("../repos.json");

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Repo {
    pub name: String,
    pub html_url: String,
    pub description: Option<String>,
    pub fork: bool,
    pub archived: Option<bool>,
    pub language: Option<String>,
    pub stargazers_count: u32,
    pub updated_at: String,
    pub pushed_at: Option<String>,
    #[serde(default)]
    pub topics: Vec<String>,
}

impl Repo {
    pub fn is_embedded(&self) -> bool {
        let name_lower = self.name.to_lowercase();
        let desc_lower = self.description.as_deref().unwrap_or("").to_lowercase();
        let lang = self.language.as_deref().unwrap_or("");

        lang.eq_ignore_ascii_case("c")
            || lang.eq_ignore_ascii_case("rust")
            || name_lower.contains("stm32")
            || name_lower.contains("pcb")
            || name_lower.contains("firmware")
            || desc_lower.contains("stm32")
            || desc_lower.contains("embedded")
            || desc_lower.contains("kicad")
            || desc_lower.contains("iar")
            || self.topics.iter().any(|t| {
                let tl = t.to_lowercase();
                tl.contains("stm32") || tl.contains("embedded") || tl.contains("firmware")
            })
    }

    pub fn relative_time(&self) -> String {
        let date_str = self.pushed_at.as_deref().unwrap_or(&self.updated_at);
        // Minimal date diff using js_sys::Date
        let target_date = js_sys::Date::new(&JsValue::from_str(date_str));
        let diff_ms = now_ms() - target_date.get_time();
        if diff_ms <= 0.0 {
            return "just now".to_string();
        }
        let secs = (diff_ms / 1000.0) as u64;
        let mins = secs / 60;
        let hours = mins / 60;
        let days = hours / 24;
        let months = days / 30;

        if months > 0 {
            format!("{}mo ago", months)
        } else if days > 0 {
            format!("{}d ago", days)
        } else if hours > 0 {
            format!("{}h ago", hours)
        } else if mins > 0 {
            format!("{}m ago", mins)
        } else {
            "just now".to_string()
        }
    }
}

pub async fn load_and_render_projects() {
    let mut source_label = "[offline snapshot]";
    let mut repos = match try_load_cached() {
        Some(cached) => {
            source_label = "[cached]";
            cached
        }
        None => match fetch_github_repos().await {
            Ok(live) => {
                source_label = "[live api]";
                cache_repos(&live);
                live
            }
            Err(_) => parse_repos_json(FALLBACK_REPOS_JSON),
        },
    };

    if repos.is_empty() {
        repos = parse_repos_json(FALLBACK_REPOS_JSON);
    }

    // Filter out forks and archived unless all are forks
    let filtered: Vec<Repo> = repos
        .into_iter()
        .filter(|r| !r.fork && !r.archived.unwrap_or(false))
        .collect();

    let mut sorted_repos = filtered;
    sorted_repos.sort_by(|a, b| {
        let a_emb = a.is_embedded();
        let b_emb = b.is_embedded();
        match (a_emb, b_emb) {
            (true, false) => std::cmp::Ordering::Less,
            (false, true) => std::cmp::Ordering::Greater,
            _ => b.updated_at.cmp(&a.updated_at),
        }
    });

    render_projects_dom(&sorted_repos, source_label);
    render_language_bar(&sorted_repos);
    update_footer_meta(&sorted_repos);
}

fn try_load_cached() -> Option<Vec<Repo>> {
    let storage = local_storage()?;
    let time_str = storage.get_item(CACHE_TIME_KEY).ok()??;
    let cached_time: f64 = time_str.parse().ok()?;
    if now_ms() - cached_time > ONE_HOUR_MS {
        return None;
    }
    let data_str = storage.get_item(CACHE_KEY).ok()??;
    let parsed: Vec<Repo> = serde_wasm_bindgen::from_value(
        js_sys::JSON::parse(&data_str).ok()?
    ).ok()?;
    Some(parsed)
}

fn cache_repos(repos: &[Repo]) {
    if let Some(storage) = local_storage() {
        if let Ok(js_val) = serde_wasm_bindgen::to_value(repos) {
            if let Ok(json_str) = js_sys::JSON::stringify(&js_val) {
                let _ = storage.set_item(CACHE_KEY, &json_str.as_string().unwrap_or_default());
                let _ = storage.set_item(CACHE_TIME_KEY, &now_ms().to_string());
            }
        }
    }
}

async fn fetch_github_repos() -> Result<Vec<Repo>, JsValue> {
    let opts = RequestInit::new();
    opts.set_method("GET");
    opts.set_mode(RequestMode::Cors);

    let url = "https://api.github.com/users/Jezali/repos?per_page=100&sort=updated";
    let request = Request::new_with_str_and_init(url, &opts)?;
    request.headers().set("Accept", "application/vnd.github.v3+json")?;

    let resp_value = JsFuture::from(crate::util::window().fetch_with_request(&request)).await?;
    let resp: Response = resp_value.dyn_into()?;
    if !resp.ok() {
        return Err(JsValue::from_str(&format!("HTTP status {}", resp.status())));
    }

    let json_value = JsFuture::from(resp.json()?).await?;
    let repos: Vec<Repo> = serde_wasm_bindgen::from_value(json_value)
        .map_err(|e| JsValue::from_str(&e.to_string()))?;
    Ok(repos)
}

fn parse_repos_json(json: &str) -> Vec<Repo> {
    if let Ok(js_val) = js_sys::JSON::parse(json) {
        if let Ok(repos) = serde_wasm_bindgen::from_value(js_val) {
            return repos;
        }
    }
    Vec::new()
}

fn render_projects_dom(repos: &[Repo], source_badge: &str) {
    if let Some(badge_el) = get_element_by_id("repos-source-badge") {
        badge_el.set_text_content(Some(source_badge));
    }

    let container = match get_element_by_id("projects-list") {
        Some(el) => el,
        None => return,
    };

    let mut html = String::new();
    for (i, repo) in repos.iter().enumerate() {
        let comp_ref = format!("U{}", i + 1);
        let lang = repo.language.as_deref().unwrap_or("TEXT");
        let desc = repo.description.as_deref().unwrap_or("No description provided.");
        let time = repo.relative_time();
        let stars = repo.stargazers_count;
        let star_text = if stars > 0 { format!(" ★ {}", stars) } else { String::new() };

        let lang_color = match lang {
            "C" => "var(--aqua)",
            "Rust" => "var(--orange)",
            "Python" => "var(--yellow)",
            "Assembly" => "var(--red)",
            _ => "var(--fg4)",
        };

        html.push_str(&format!(
            r#"<a class="project-row" href="{url}" target="_blank" rel="noopener noreferrer">
                <div class="proj-ref">{comp_ref}</div>
                <div class="proj-content">
                    <div class="proj-title-row">
                        <span class="proj-name">{name}</span>
                        <span class="proj-meta">
                            <span class="lang-dot" style="background-color: {lang_color}"></span>
                            <span class="proj-lang">{lang}</span>
                            <span class="proj-stars">{star_text}</span>
                            <span class="proj-time">{time}</span>
                        </span>
                    </div>
                    <div class="proj-desc">{desc}</div>
                </div>
                <div class="proj-arrow">→</div>
            </a>"#,
            url = repo.html_url,
            comp_ref = comp_ref,
            name = repo.name,
            lang_color = lang_color,
            lang = lang,
            star_text = star_text,
            time = time,
            desc = desc
        ));
    }

    container.set_inner_html(&html);
}

fn render_language_bar(repos: &[Repo]) {
    let container = match get_element_by_id("lang-breakdown") {
        Some(el) => el,
        None => return,
    };

    let mut counts: HashMap<String, usize> = HashMap::new();
    let mut total = 0;
    for r in repos {
        if let Some(ref l) = r.language {
            *counts.entry(l.clone()).or_insert(0) += 1;
            total += 1;
        }
    }

    if total == 0 {
        return;
    }

    let mut bar_html = String::from(r#"<div class="lang-bar">"#);
    let mut legend_html = String::from(r#"<div class="lang-legend">"#);

    let colors = [
        ("C", "var(--aqua)"),
        ("Rust", "var(--orange)"),
        ("Python", "var(--yellow)"),
        ("Assembly", "var(--red)"),
        ("Other", "var(--fg4)"),
    ];

    for (lang, count) in &counts {
        let pct = (*count as f64 / total as f64) * 100.0;
        let color = colors.iter()
            .find(|(l, _)| l == lang)
            .map(|(_, c)| *c)
            .unwrap_or("var(--fg4)");

        bar_html.push_str(&format!(
            r#"<div class="lang-segment" style="width: {pct:.1}%; background-color: {color};" title="{lang}: {pct:.0}%"></div>"#,
            pct = pct,
            color = color,
            lang = lang
        ));

        legend_html.push_str(&format!(
            r#"<span class="legend-item"><span class="lang-dot" style="background-color: {color};"></span> {lang} ({pct:.0}%)</span> "#,
            color = color,
            lang = lang,
            pct = pct
        ));
    }

    bar_html.push_str("</div>");
    legend_html.push_str("</div>");

    container.set_inner_html(&format!("{}{}", bar_html, legend_html));
}

fn update_footer_meta(repos: &[Repo]) {
    if let Some(first) = repos.first() {
        if let Some(el) = get_element_by_id("footer-commit") {
            let time = first.relative_time();
            el.set_text_content(Some(&format!("last push: {} ({})", first.name, time)));
        }
    }
}
