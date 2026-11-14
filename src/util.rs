use wasm_bindgen::prelude::*;
use web_sys::{Document, Element, HtmlElement, Storage, Window};

pub fn window() -> Window {
    web_sys::window().expect("no global `window` exists")
}

pub fn document() -> Document {
    window().document().expect("should have a document on window")
}

pub fn local_storage() -> Option<Storage> {
    window().local_storage().ok().flatten()
}

pub fn session_storage() -> Option<Storage> {
    window().session_storage().ok().flatten()
}

pub fn get_element_by_id(id: &str) -> Option<Element> {
    document().get_element_by_id(id)
}

pub fn get_html_element(id: &str) -> Option<HtmlElement> {
    get_element_by_id(id).and_then(|el| el.dyn_into::<HtmlElement>().ok())
}

pub fn now_ms() -> f64 {
    js_sys::Date::now()
}

pub fn copy_to_clipboard(text: &str) {
    let nav = window().navigator();
    let clipboard = nav.clipboard();
    let _ = clipboard.write_text(text);
}

pub fn is_reduced_motion() -> bool {
    window()
        .match_media("(prefers-reduced-motion: reduce)")
        .ok()
        .flatten()
        .map(|m| m.matches())
        .unwrap_or(false)
}

pub fn is_fx_enabled() -> bool {
    if is_reduced_motion() {
        return false;
    }
    if let Some(storage) = local_storage() {
        if let Ok(Some(val)) = storage.get_item("jezali_fx") {
            return val == "1" || val == "true";
        }
    }
    true
}

pub fn set_fx_enabled(val: bool) {
    if let Some(storage) = local_storage() {
        let _ = storage.set_item("jezali_fx", if val { "1" } else { "0" });
    }
}
