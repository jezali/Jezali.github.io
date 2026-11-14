use wasm_bindgen::prelude::*;
use web_sys::{KeyboardEvent, MouseEvent};
use std::cell::RefCell;
use std::rc::Rc;
use crate::util::{document, get_element_by_id, local_storage, window};

const EGGS_KEY: &str = "jezali_eggs_found";
const TOTAL_EGGS: usize = 20;

pub fn get_egg_count() -> usize {
    if let Some(storage) = local_storage() {
        if let Ok(Some(val)) = storage.get_item(EGGS_KEY) {
            let eggs: Vec<&str> = val.split(',').filter(|s| !s.is_empty()).collect();
            return eggs.len();
        }
    }
    0
}

pub fn record_egg(name: &str) {
    if let Some(storage) = local_storage() {
        let mut list: Vec<String> = storage
            .get_item(EGGS_KEY)
            .ok()
            .flatten()
            .map(|v| v.split(',').filter(|s| !s.is_empty()).map(|s| s.to_string()).collect())
            .unwrap_or_default();

        if !list.iter().any(|e| e == name) {
            list.push(name.to_string());
            let _ = storage.set_item(EGGS_KEY, &list.join(","));
            update_egg_counter_dom(list.len());
        }
    }
}

pub fn update_egg_counter_dom(count: usize) {
    if let Some(el) = get_element_by_id("eggs-counter") {
        el.set_text_content(Some(&format!("eggs found: {}/{}", count, TOTAL_EGGS)));
    }
    // Also update cyberpsychosis indicator if 100%
    if count >= TOTAL_EGGS {
        if let Some(moon) = get_element_by_id("footer-moon") {
            moon.set_class_name("moon-visible");
        }
    }
}

pub fn trigger_hardfault() {
    record_egg("deadbeef");
    let dump = r#"<div class="hardfault-box">
*** HARDFAULT DETECTED ***
R0  = 0x20000100  R1  = 0x00000000  R2  = 0x40020000  R3  = 0xDEADBEEF
R12 = 0x08001234  LR  = 0x08000A1F  PC  = 0x08000B22  xPSR= 0x61000000
HFSR= 0x40000000  CFSR= 0x00010000  BFAR= 0xDEADBEEF
Status: BusFault on precise data bus error
Halting core... rebooting system in 3s...
</div>"#;

    if let Some(out) = get_element_by_id("term-output") {
        let div = document().create_element("div").unwrap();
        div.set_inner_html(dump);
        let _ = out.append_child(&div);
        out.set_scroll_top(out.scroll_height());
    }

    let win = window();
    let cb = Closure::<dyn Fn()>::wrap(Box::new(move || {
        let _ = window().location().reload();
    }));
    let _ = win.set_timeout_with_callback_and_timeout_and_arguments_0(cb.as_ref().unchecked_ref(), 3000);
    cb.forget();
}

pub fn init_easter_eggs() -> Result<(), JsValue> {
    update_egg_counter_dom(get_egg_count());

    // 1. Konami Code Listener & Global 'wake up samurai'
    {
        let konami_seq = ["ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown", "ArrowLeft", "ArrowRight", "ArrowLeft", "ArrowRight", "b", "a"];
        let buffer: Rc<RefCell<Vec<String>>> = Rc::new(RefCell::new(Vec::new()));
        let samurai_buf: Rc<RefCell<String>> = Rc::new(RefCell::new(String::new()));

        let on_keydown = Closure::<dyn Fn(KeyboardEvent)>::wrap(Box::new(move |e: KeyboardEvent| {
            let key = e.key();

            // Track Konami
            let mut buf = buffer.borrow_mut();
            buf.push(key.clone());
            if buf.len() > konami_seq.len() {
                buf.remove(0);
            }
            if buf.len() == konami_seq.len() && buf.iter().zip(konami_seq.iter()).all(|(a, b)| a.eq_ignore_ascii_case(b)) {
                buf.clear();
                record_egg("konami");
                open_netrunner_breach();
            }

            // Track 'wake up samurai'
            let mut sbuf = samurai_buf.borrow_mut();
            if key.len() == 1 {
                sbuf.push_str(&key.to_lowercase());
                if sbuf.len() > 30 {
                    sbuf.drain(..10);
                }
                if sbuf.ends_with("wake up samurai") {
                    sbuf.clear();
                    record_egg("samurai");
                    if let Some(term) = get_element_by_id("term-input") {
                        let _ = term.dyn_into::<web_sys::HtmlInputElement>().map(|i| {
                            i.set_value("samurai");
                            let _ = i.focus();
                        });
                    }
                }
            }
        }));

        let _ = window().add_event_listener_with_callback("keydown", on_keydown.as_ref().unchecked_ref());
        on_keydown.forget();
    }

    // 2. Avatar Clicks (Akira 7-clicks) & Avatar LED
    {
        let clicks = Rc::new(RefCell::new(0));
        if let Some(avatar_el) = get_element_by_id("hero-avatar") {
            let clicks_clone = Rc::clone(&clicks);
            let on_click = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
                let mut c = clicks_clone.borrow_mut();
                *c += 1;
                if *c >= 7 {
                    *c = 0;
                    record_egg("akira");
                    trigger_akira_capsule();
                }
            }));
            let _ = avatar_el.add_event_listener_with_callback("click", on_click.as_ref().unchecked_ref());
            on_click.forget();
        }

        // Avatar LED Click toggle
        if let Some(led_el) = get_element_by_id("avatar-led") {
            let on_led_click = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
                record_egg("led_toggle");
                if let Some(led) = get_element_by_id("avatar-led") {
                    let cur = led.class_name();
                    if cur.contains("led-off") {
                        led.set_class_name("avatar-led led-blink");
                    } else {
                        led.set_class_name("avatar-led led-off");
                    }
                }
            }));
            let _ = led_el.add_event_listener_with_callback("click", on_led_click.as_ref().unchecked_ref());
            on_led_click.forget();
        }
    }

    // 3. Avatar Enhance (Hover 3 seconds)
    {
        let timer_id: Rc<RefCell<Option<i32>>> = Rc::new(RefCell::new(None));
        if let Some(avatar_el) = get_element_by_id("hero-avatar") {
            let timer_enter = Rc::clone(&timer_id);
            let on_enter = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
                let timer = Rc::clone(&timer_enter);
                let cb = Closure::<dyn Fn()>::wrap(Box::new(move || {
                    record_egg("enhance");
                    if let Some(hud) = get_element_by_id("enhance-hud") {
                        hud.set_class_name("enhance-hud visible");
                    }
                }));
                let tid = window()
                    .set_timeout_with_callback_and_timeout_and_arguments_0(cb.as_ref().unchecked_ref(), 3000)
                    .unwrap_or(0);
                cb.forget();
                *timer.borrow_mut() = Some(tid);
            }));
            let _ = avatar_el.add_event_listener_with_callback("mouseenter", on_enter.as_ref().unchecked_ref());
            on_enter.forget();

            let timer_leave = Rc::clone(&timer_id);
            let on_leave = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
                if let Some(tid) = *timer_leave.borrow() {
                    window().clear_timeout_with_handle(tid);
                }
                *timer_leave.borrow_mut() = None;
                if let Some(hud) = get_element_by_id("enhance-hud") {
                    hud.set_class_name("enhance-hud");
                }
            }));
            let _ = avatar_el.add_event_listener_with_callback("mouseleave", on_leave.as_ref().unchecked_ref());
            on_leave.forget();
        }
    }

    // 4. Footer Hex 0xDEADBEEF 3-clicks
    {
        let hex_clicks = Rc::new(RefCell::new(0));
        if let Some(hex_el) = get_element_by_id("footer-deadbeef") {
            let hc = Rc::clone(&hex_clicks);
            let on_hex = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
                let mut c = hc.borrow_mut();
                *c += 1;
                if *c >= 3 {
                    *c = 0;
                    trigger_hardfault();
                }
            }));
            let _ = hex_el.add_event_listener_with_callback("click", on_hex.as_ref().unchecked_ref());
            on_hex.forget();
        }
    }

    // 5. Footer Eye -> Voight-Kampff trigger
    {
        if let Some(eye_el) = get_element_by_id("footer-vk-eye") {
            let on_eye = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
                if let Some(inp) = get_element_by_id("term-input") {
                    let _ = inp.dyn_into::<web_sys::HtmlInputElement>().map(|i| {
                        i.set_value("vk");
                        let _ = i.focus();
                    });
                }
                // scroll to terminal
                if let Some(term_sec) = get_element_by_id("sec-terminal") {
                    term_sec.scroll_into_view();
                }
            }));
            let _ = eye_el.add_event_listener_with_callback("click", on_eye.as_ref().unchecked_ref());
            on_eye.forget();
        }
    }

    // 6. Resistor hover
    {
        if let Some(resistor_el) = get_element_by_id("resistor-r12") {
            let on_res_enter = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
                record_egg("resistor");
                if let Some(tip) = get_element_by_id("resistor-tooltip") {
                    tip.set_text_content(Some("Jezali = 4.7kΩ ±5% [Yellow-Violet-Red-Gold]"));
                }
            }));
            let _ = resistor_el.add_event_listener_with_callback("mouseenter", on_res_enter.as_ref().unchecked_ref());
            on_res_enter.forget();
        }
    }

    // 7. Origami Unicorn: scroll to bottom + 10s idle
    {
        let unicorn_timer: Rc<RefCell<Option<i32>>> = Rc::new(RefCell::new(None));
        let unicorn_revealed = Rc::new(RefCell::new(false));

        let ut = Rc::clone(&unicorn_timer);
        let ur = Rc::clone(&unicorn_revealed);

        let on_scroll = Closure::<dyn Fn()>::wrap(Box::new(move || {
            if *ur.borrow() {
                return;
            }
            let win = window();
            let scroll_y = win.scroll_y().unwrap_or(0.0);
            let inner_h = win.inner_height().ok().and_then(|v| v.as_f64()).unwrap_or(0.0);
            let doc_h = document().body().map(|b| b.scroll_height() as f64).unwrap_or(0.0);

            if scroll_y + inner_h >= doc_h - 40.0 {
                // Near bottom
                if ut.borrow().is_none() {
                    let ur_cb = Rc::clone(&ur);
                    let cb = Closure::<dyn Fn()>::wrap(Box::new(move || {
                        *ur_cb.borrow_mut() = true;
                        record_egg("unicorn");
                        if let Some(u) = get_element_by_id("origami-unicorn") {
                            u.set_class_name("origami-unicorn visible");
                        }
                    }));
                    let tid = window()
                        .set_timeout_with_callback_and_timeout_and_arguments_0(cb.as_ref().unchecked_ref(), 10000)
                        .unwrap_or(0);
                    cb.forget();
                    *ut.borrow_mut() = Some(tid);
                }
            } else {
                if let Some(tid) = *ut.borrow() {
                    window().clear_timeout_with_handle(tid);
                    *ut.borrow_mut() = None;
                }
            }
        }));
        let _ = window().add_event_listener_with_callback("scroll", on_scroll.as_ref().unchecked_ref());
        on_scroll.forget();
    }

    // 8. Off-world ad ticker (rare 1-in-4 visit)
    {
        if js_sys::Math::random() < 0.25 {
            if let Some(ad) = get_element_by_id("offworld-ad") {
                ad.set_class_name("offworld-ad visible");
                record_egg("offworld_ad");
            }
        }
        if let Some(close_btn) = get_element_by_id("offworld-close") {
            let on_close = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
                if let Some(ad) = get_element_by_id("offworld-ad") {
                    ad.set_class_name("offworld-ad");
                }
            }));
            let _ = close_btn.add_event_listener_with_callback("click", on_close.as_ref().unchecked_ref());
            on_close.forget();
        }
    }

    // 9. Breach protocol UI handlers
    setup_breach_ui();

    Ok(())
}

fn trigger_akira_capsule() {
    let doc_el = document().document_element().unwrap();
    let _ = doc_el.set_attribute("data-akira", "active");
    if let Some(hud) = get_element_by_id("akira-hud") {
        hud.set_class_name("akira-hud visible");
    }
    let cb = Closure::<dyn Fn()>::wrap(Box::new(move || {
        let doc_el = document().document_element().unwrap();
        let _ = doc_el.remove_attribute("data-akira");
        if let Some(hud) = get_element_by_id("akira-hud") {
            hud.set_class_name("akira-hud");
        }
    }));
    let _ = window().set_timeout_with_callback_and_timeout_and_arguments_0(cb.as_ref().unchecked_ref(), 4000);
    cb.forget();
}

fn open_netrunner_breach() {
    if let Some(overlay) = get_element_by_id("breach-modal") {
        overlay.set_class_name("breach-modal open");
    }
}

fn setup_breach_ui() {
    let target_seq = ["1C", "E9", "BD", "55"];
    let entered_seq: Rc<RefCell<Vec<String>>> = Rc::new(RefCell::new(Vec::new()));

    let doc = document();
    let buttons = doc.query_selector_all(".breach-cell").unwrap();
    for i in 0..buttons.length() {
        if let Some(node) = buttons.get(i) {
            if let Ok(el) = node.dyn_into::<web_sys::HtmlElement>() {
                let seq = Rc::clone(&entered_seq);
                let code = el.get_attribute("data-code").unwrap_or_default();
                let el_clone = el.clone();
                let on_cell_click = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
                    let mut s = seq.borrow_mut();
                    s.push(code.clone());
                    el_clone.set_class_name("breach-cell selected");

                    if let Some(display) = get_element_by_id("breach-seq-display") {
                        display.set_text_content(Some(&s.join(" ")));
                    }

                    if s.len() >= target_seq.len() {
                        let success = s.iter().zip(target_seq.iter()).all(|(a, b)| a == b);
                        if success {
                            record_egg("breach_success");
                            if let Some(status) = get_element_by_id("breach-status") {
                                status.set_inner_html(r#"<span class="breach-win">ICE BREACHED // ACCESS GRANTED</span>"#);
                            }
                            let doc_el = document().document_element().unwrap();
                            let _ = doc_el.set_attribute("data-theme", "red");
                            let cb = Closure::<dyn Fn()>::wrap(Box::new(move || {
                                if let Some(overlay) = get_element_by_id("breach-modal") {
                                    overlay.set_class_name("breach-modal");
                                }
                                let doc_el = document().document_element().unwrap();
                                let _ = doc_el.remove_attribute("data-theme");
                            }));
                            let _ = window().set_timeout_with_callback_and_timeout_and_arguments_0(cb.as_ref().unchecked_ref(), 2500);
                            cb.forget();
                        } else {
                            if let Some(status) = get_element_by_id("breach-status") {
                                status.set_inner_html(r#"<span class="breach-fail">BREACH FAILED // BUFFER OVERFLOW</span>"#);
                            }
                            s.clear();
                        }
                    }
                }));
                let _ = el.add_event_listener_with_callback("click", on_cell_click.as_ref().unchecked_ref());
                on_cell_click.forget();
            }
        }
    }

    if let Some(close_btn) = get_element_by_id("breach-close") {
        let on_close = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
            if let Some(overlay) = get_element_by_id("breach-modal") {
                overlay.set_class_name("breach-modal");
            }
        }));
        let _ = close_btn.add_event_listener_with_callback("click", on_close.as_ref().unchecked_ref());
        on_close.forget();
    }
}
