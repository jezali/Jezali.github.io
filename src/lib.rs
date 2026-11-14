use wasm_bindgen::prelude::*;
use web_sys::{HtmlElement, MouseEvent};
use std::cell::RefCell;
use std::rc::Rc;

mod util;
mod canvas;
mod github;
mod terminal;
mod eggs;

use util::{document, get_element_by_id, get_html_element, session_storage, is_reduced_motion, is_fx_enabled, set_fx_enabled, copy_to_clipboard, window};
use canvas::init_canvas;
use github::load_and_render_projects;
use terminal::init_terminal;
use eggs::init_easter_eggs;

#[wasm_bindgen(start)]
pub fn main_js() -> Result<(), JsValue> {
    // 1. Boot sequence handling
    run_boot_sequence();

    // 2. Initialize PCB trace canvas background
    let canvas_state = init_canvas()?;

    // 3. Load & render GitHub projects
    wasm_bindgen_futures::spawn_local(async {
        load_and_render_projects().await;
    });

    // 4. Initialize Terminal
    init_terminal(canvas_state)?;

    // 5. Initialize Easter eggs
    init_easter_eggs()?;

    // 6. Contact Copy buttons
    init_contact_copy();

    // 7. Footer controls (FX toggle, Theme toggle)
    init_footer_controls();

    // 8. Progressive reveal with IntersectionObserver
    init_section_observer();

    Ok(())
}

fn run_boot_sequence() {
    let already_booted = session_storage()
        .and_then(|s| s.get_item("jezali_booted").ok().flatten())
        .is_some();

    if already_booted || is_reduced_motion() {
        finish_boot();
        return;
    }

    let boot_banner = match get_element_by_id("boot-sequence") {
        Some(el) => el,
        None => return,
    };

    let lines = [
        "JEZALI-OS v0.1 (stm32f4, 168MHz)",
        "[ OK ] clock tree (168MHz HSE/PLL)",
        "[ OK ] gpio (ports A-E configured)",
        "[ OK ] uart @ 115200 8N1",
        "[ .. ] loading engineer profile...",
    ];

    let line_idx = Rc::new(RefCell::new(0));
    let timer_id: Rc<RefCell<Option<i32>>> = Rc::new(RefCell::new(None));

    // Allow skip on click or key
    {
        let t_clone = Rc::clone(&timer_id);
        let on_skip = Closure::<dyn Fn()>::wrap(Box::new(move || {
            if let Some(tid) = *t_clone.borrow() {
                window().clear_timeout_with_handle(tid);
            }
            finish_boot();
        }));
        let _ = boot_banner.add_event_listener_with_callback("click", on_skip.as_ref().unchecked_ref());
        on_skip.forget();
    }

    let t_clone = Rc::clone(&timer_id);
    let step_cb: Rc<RefCell<Option<Closure<dyn Fn()>>>> = Rc::new(RefCell::new(None));
    let step_cb_clone = Rc::clone(&step_cb);

    *step_cb.borrow_mut() = Some(Closure::wrap(Box::new(move || {
        let mut idx = line_idx.borrow_mut();
        if *idx < lines.len() {
            if let Some(container) = get_element_by_id("boot-lines") {
                let div = document().create_element("div").unwrap();
                div.set_class_name("boot-line");
                div.set_text_content(Some(lines[*idx]));
                let _ = container.append_child(&div);
            }
            *idx += 1;
            let tid = window()
                .set_timeout_with_callback_and_timeout_and_arguments_0(
                    step_cb_clone.borrow().as_ref().unwrap().as_ref().unchecked_ref(),
                    220,
                )
                .unwrap_or(0);
            *t_clone.borrow_mut() = Some(tid);
        } else {
            finish_boot();
        }
    }) as Box<dyn Fn()>));

    let tid = window()
        .set_timeout_with_callback_and_timeout_and_arguments_0(
            step_cb.borrow().as_ref().unwrap().as_ref().unchecked_ref(),
            100,
        )
        .unwrap_or(0);
    *timer_id.borrow_mut() = Some(tid);
}

fn finish_boot() {
    if let Some(s) = session_storage() {
        let _ = s.set_item("jezali_booted", "1");
    }
    if let Some(boot) = get_element_by_id("boot-sequence") {
        boot.set_class_name("boot-sequence hidden");
    }
    if let Some(hero) = get_element_by_id("hero-container") {
        hero.set_class_name("hero-container visible");
    }
}

fn init_contact_copy() {
    let doc = document();
    let copy_buttons = doc.query_selector_all(".copy-trigger").unwrap();
    for i in 0..copy_buttons.length() {
        if let Some(node) = copy_buttons.get(i) {
            if let Ok(el) = node.dyn_into::<HtmlElement>() {
                let text_to_copy = el.get_attribute("data-copy").unwrap_or_default();
                let confirm_id = el.get_attribute("data-confirm").unwrap_or_default();
                let on_click = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
                    copy_to_clipboard(&text_to_copy);
                    if let Some(badge) = get_element_by_id(&confirm_id) {
                        badge.set_class_name("copied-badge visible");
                        let b_clone = badge.clone();
                        let cb = Closure::<dyn Fn()>::wrap(Box::new(move || {
                            b_clone.set_class_name("copied-badge");
                        }));
                        let _ = window().set_timeout_with_callback_and_timeout_and_arguments_0(cb.as_ref().unchecked_ref(), 1500);
                        cb.forget();
                    }
                }));
                let _ = el.add_event_listener_with_callback("click", on_click.as_ref().unchecked_ref());
                on_click.forget();
            }
        }
    }
}

fn init_footer_controls() {
    // FX toggle
    if let Some(btn) = get_element_by_id("fx-toggle") {
        let update_label = |b: &HtmlElement| {
            let active = is_fx_enabled();
            b.set_text_content(Some(if active { "[fx: on]" } else { "[fx: off]" }));
        };
        if let Ok(hel) = btn.clone().dyn_into::<HtmlElement>() {
            update_label(&hel);
        }

        let on_click = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
            let current = is_fx_enabled();
            set_fx_enabled(!current);
            if let Some(b) = get_html_element("fx-toggle") {
                b.set_text_content(Some(if !current { "[fx: on]" } else { "[fx: off]" }));
            }
        }));
        let _ = btn.add_event_listener_with_callback("click", on_click.as_ref().unchecked_ref());
        on_click.forget();
    }

    // Theme toggle
    if let Some(btn) = get_element_by_id("theme-toggle") {
        let on_click = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
            let doc_el = document().document_element().unwrap();
            let current = doc_el.get_attribute("data-theme").unwrap_or_default();
            let new_theme = if current == "aqua" { "orange" } else { "aqua" };
            let _ = doc_el.set_attribute("data-theme", new_theme);
            if let Some(b) = get_html_element("theme-toggle") {
                b.set_text_content(Some(&format!("[theme: {}]", new_theme)));
            }
        }));
        let _ = btn.add_event_listener_with_callback("click", on_click.as_ref().unchecked_ref());
        on_click.forget();
    }
}

fn init_section_observer() {
    // Progressive reveal using IntersectionObserver
    let doc = document();
    let sections = doc.query_selector_all(".observed-section").unwrap();

    let callback = Closure::<dyn Fn(js_sys::Array, web_sys::IntersectionObserver)>::wrap(Box::new(
        move |entries: js_sys::Array, _obs: web_sys::IntersectionObserver| {
            for i in 0..entries.length() {
                let entry: web_sys::IntersectionObserverEntry = entries.get(i).unchecked_into();
                if entry.is_intersecting() {
                    let target = entry.target();
                    let cur_class = target.class_name();
                    if !cur_class.contains("section-revealed") {
                        target.set_class_name(&format!("{} section-revealed", cur_class));
                    }
                }
            }
        },
    ));

    if let Ok(observer) = web_sys::IntersectionObserver::new(callback.as_ref().unchecked_ref()) {
        for i in 0..sections.length() {
            if let Some(node) = sections.get(i) {
                if let Ok(el) = node.dyn_into::<web_sys::Element>() {
                    observer.observe(&el);
                }
            }
        }
        callback.forget();
    }
}
