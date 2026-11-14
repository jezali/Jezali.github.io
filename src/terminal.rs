use wasm_bindgen::prelude::*;
use web_sys::{HtmlInputElement, KeyboardEvent, MouseEvent};
use std::cell::RefCell;
use std::rc::Rc;
use crate::util::{document, get_element_by_id};
use crate::eggs::{record_egg, get_egg_count, trigger_hardfault};
use crate::canvas::CanvasState;

pub struct TerminalState {
    history: Vec<String>,
    history_idx: usize,
    canvas_ref: Rc<RefCell<CanvasState>>,
    vk_step: Option<usize>,
    cells_step: usize,
}

impl TerminalState {
    pub fn new(canvas_ref: Rc<RefCell<CanvasState>>) -> Self {
        Self {
            history: Vec::new(),
            history_idx: 0,
            canvas_ref,
            vk_step: None,
            cells_step: 0,
        }
    }

    pub fn execute(&mut self, input: &str) {
        let trimmed = input.trim();
        if trimmed.is_empty() {
            return;
        }

        self.history.push(trimmed.to_string());
        self.history_idx = self.history.len();

        append_terminal_line(&format!("<span class=\"term-prompt\">jezali@nightcity:~$</span> {}", trimmed));

        // If in Voight-Kampff test mode
        if let Some(step) = self.vk_step {
            self.handle_vk_answer(trimmed, step);
            return;
        }

        let parts: Vec<&str> = trimmed.split_whitespace().collect();
        let cmd = parts[0].to_lowercase();
        let args = &parts[1..];

        match cmd.as_str() {
            "help" => {
                append_terminal_line(r#"<span class="term-hl">COMMANDS:</span>
  whoami         display user identity (--nexus for replicant specs)
  ls             list directory entries
  cat &lt;file&gt;     display file content (e.g. cat about)
  projects       list active projects
  contact        show communication pinout
  neofetch       system and hardware telemetry
  clear          clear screen
  theme          toggle accent (orange / aqua)
  vk             initiate Voight-Kampff test
  samurai        wake up
  rain           toggle canvas pixel rain (or 'rain off')
  eggs           show discovered easter egg count
  [classified]   hidden netrunner commands..."#);
            }

            "whoami" => {
                if args.contains(&"--nexus") {
                    record_egg("nexus");
                    append_terminal_line(r#"<span class="term-hl">-- TYRELL CORP SPEC SHEET --</span>
Model: Nexus-JZL (Physical A, Mental A)
Incept Date: 2022-04-12
Function: Embedded Systems / Cortex-M Firmware
Lifespan: 4 years -&gt; [UNLIMITED: patched via custom bootloader]"#);
                } else {
                    append_terminal_line("Jezali (Hossein Monjezi) - Embedded Systems Engineer\nSpecialization: C, STM32 firmware, PCB layout.");
                }
            }

            "ls" => {
                append_terminal_line("about.txt   stack.map   projects/   contact.pin   secret_keys.bin   // firmware.bin");
            }

            "cat" => {
                let target = args.first().copied().unwrap_or("");
                match target {
                    "about" | "about.txt" => {
                        append_terminal_line("ABOUT:\nFirmware engineer specializing in bare-metal and HAL C on STM32.\nDesigning custom hardware, troubleshooting timing with logic analyzers,\nand enduring the 2 AM debug cycle.");
                    }
                    "stack" | "stack.map" | "stack.txt" => {
                        append_terminal_line("STACK:\nLANG: C, Rust (WASM), ARM Assembly\nMCU: STM32 (F1 / F4)\nTOOLS: GCC ARM, CMake, OpenOCD\nDEBUG: ST-Link, Logic Analyzer, Oscilloscope");
                    }
                    "contact" | "contact.pin" | "contact.txt" => {
                        append_terminal_line("CONTACT:\nEMAIL: jezali.jakaloo@protonmail.com\nTG:    @unsaltedchickenbreast\nGH:    github.com/Jezali");
                    }
                    "secret_keys.bin" | "secret.bin" => {
                        record_egg("secret_bin");
                        append_terminal_line("00000000: 4b 4f 4e 41 4d 49 5f 43 4f 44 45 3a 20 55 55 44  KONAMI_CODE: UUD\n00000010: 44 4c 52 4c 52 42 41 00 00 00 00 00 00 00 00 00  DLRBA...........\n[ENCRYPTED PAYLOAD]");
                    }
                    _ => {
                        append_terminal_line(&format!("cat: {}: No such file or directory", target));
                    }
                }
            }

            "projects" => {
                append_terminal_line("ACTIVE REPOSITORIES:\n1. STM32F407VGT6_C_SampleCodes [C] - Comprehensive hardware driver suite\n2. STM32F407VGT6_C_Menu [C] - Embedded LCD menu system\nRun 'cat projects' or inspect section [ 0x03 ] above.");
            }

            "contact" => {
                append_terminal_line("PINOUT J1:\nPIN 1 (EM)  : jezali.jakaloo@protonmail.com (mailto:jezali.jakaloo@protonmail.com)\nPIN 2 (TG)  : @unsaltedchickenbreast (https://t.me/unsaltedchickenbreast)\nPIN 3 (GH)  : github.com/Jezali");
            }

            "neofetch" => {
                append_terminal_line(r#"<span class="term-hl">        .---.        jezali@nightcity</span>
<span class="term-hl">       /     \       ----------------</span>
<span class="term-hl">      | () () |      OS:</span> Jezali-OS v0.1 (stm32f4)
<span class="term-hl">       \  _  /       HOST:</span> STM32F407VGT6 @ 168MHz
<span class="term-hl">        '---'        KERNEL:</span> Baremetal / FreeRTOS
<span class="term-hl">      /|     |\      ARCH:</span> ARM Cortex-M4 (w/ FPU)
<span class="term-hl">     / |     | \     MEMORY:</span> 192KB SRAM / 1024KB Flash
<span class="term-hl">    *  |_____|  *    UPTIME:</span> 2am debug cycle
<span class="term-hl">       |  |  |       SHELL:</span> nightcity-sh
<span class="term-hl">       |  |  |       COMPILER:</span> arm-none-eabi-gcc 13.2"#);
            }

            "clear" => {
                if let Some(out) = get_element_by_id("term-output") {
                    out.set_inner_html("");
                }
            }

            "theme" => {
                toggle_theme();
            }

            "samurai" | "wake" => {
                record_egg("samurai");
                append_terminal_line(r#"<span class="term-red">Wake the f*** up, Samurai. We have a city to burn.</span>
-----------------------------------/\----_/\----------------
[HEARTBEAT DETECTED: 142 BPM]"#);
            }

            "afterlife" => {
                record_egg("afterlife");
                append_terminal_line(r#"<span class="term-hl">--- THE AFTERLIFE MENU ---</span>
1. Johnny Silverhand: Tequila on the rocks, splash of cerveza, chili garnish.
2. Jackie Welles: Shot of vodka on the rocks, lime juice, ginger beer, dash of love.
3. David Martinez: Vodka on the rocks, dash of NiCola."#);
            }

            "johnny" => {
                record_egg("johnny");
                append_terminal_line("<span class=\"term-yellow\">\"Wake up, rockerboy. Time's ticking.\" - Johnny Silverhand</span>");
            }

            "delamain" => {
                record_egg("delamain");
                append_terminal_line("<span class=\"term-aqua\">\"Greetings, valued Excelsior customer. Delamain cab services at your disposal. Where to?\"</span>");
            }

            "edgerunner" => {
                record_egg("edgerunner");
                let count = get_egg_count();
                let pct = ((count as f64 / 20.0) * 100.0).min(100.0) as usize;
                let filled = pct / 10;
                let empty = 10 - filled;
                let bar = format!("[{}{}] {}%", "█".repeat(filled), "░".repeat(empty), pct);

                if pct >= 100 {
                    append_terminal_line(&format!("<span class=\"term-red\">CYBERPSYCHOSIS: {}</span>\n<span class=\"term-red\">*** FLATLINE ***</span>\n[MOON VISIBLE ON THE HORIZON]", bar));
                } else {
                    append_terminal_line(&format!("CYBERPSYCHOSIS METER: {}\nSymptoms nominal. Keep exploring to push tolerance.", bar));
                }
            }

            "ghost" => {
                record_egg("ghost");
                append_terminal_line(r#"ghost: detected
shell: STM32F407
Section 9: Public Security Section 9 stand by."#);
            }

            "ghost-dive" => {
                record_egg("ghost_dive");
                let mut c = self.canvas_ref.borrow_mut();
                c.ghost_dive_active = !c.ghost_dive_active;
                let status = if c.ghost_dive_active { "ENGAGED" } else { "DISENGAGED" };
                append_terminal_line(&format!("Ghost-dive neural link: {}", status));
            }

            "tetsuo" => {
                record_egg("tetsuo");
                append_terminal_line(r#"<span class="term-red">
 _  __     _   _ _____ ____    _    _ 
| |/ /    / \ | | ____|  _ \  / \  | |
| ' /    / _ \| |  _| | | | |/ _ \ | |
| . \   / ___ \ | |___| |_| / ___ \|_|
|_|\_\ /_/   \_\_____|____//_/   \_(_)
</span>"#);
            }

            "lain" => {
                record_egg("lain");
                append_terminal_line("<span class=\"term-aqua\">\"present day... present time... hahaha\"</span>");
                trigger_lain_cursor();
            }

            "augment" => {
                record_egg("augment");
                append_terminal_line(r#"NEURAL & HARDWARE AUGMENTATIONS:
[C Driver Suite: v11] [STM32-F4 Core: 168MHz] [KiCad PCB Engine: v8]
[Optics: Logic Analyzer 24MHz] [Coffee Infusion: 98.4%]"#);
            }

            "vk" => {
                record_egg("vk");
                self.vk_step = Some(1);
                append_terminal_line(r#"<span class="term-hl">--- VOIGHT-KAMPFF PROTOCOL INITIATED ---</span>
A flat optical sensor is monitoring pupil dilation.
Q1: You're in a desert walking along in the sand when you look down and see a tortoise crawling toward you. You reach down and flip it on its back. The tortoise lies on its back, its belly baking in the hot sun, beating its legs trying to turn itself over, but it can't, not without your help. But you're not helping. Why is that?
(Type your response):"#);
            }

            "cells" => {
                record_egg("cells");
                self.cells_step += 1;
                match self.cells_step % 3 {
                    1 => append_terminal_line("Cells.\n<span class=\"term-hl\">&gt; Interlinked.</span>"),
                    2 => append_terminal_line("Within cells interlinked.\n<span class=\"term-hl\">&gt; Within cells interlinked.</span>"),
                    _ => append_terminal_line("A system of cells interlinked within cells interlinked within one stem.\n<span class=\"term-hl\">&gt; And dreadfully distinct against the dark.</span>"),
                }
            }

            "rain" => {
                record_egg("rain");
                let mut c = self.canvas_ref.borrow_mut();
                if args.contains(&"off") {
                    c.rain_active = false;
                    append_terminal_line("Rain: stopped.");
                } else {
                    c.rain_active = true;
                    append_terminal_line("<span class=\"term-aqua\">tears in rain.</span>");
                }
            }

            "la" => {
                record_egg("la");
                if let Some(el) = get_element_by_id("footer-la-time") {
                    el.set_text_content(Some("NOV 2019 // LOS ANGELES"));
                }
                append_terminal_line("Timestamp set to: NOV 2019 // LOS ANGELES");
            }

            "0xdeadbeef" => {
                record_egg("deadbeef");
                trigger_hardfault();
            }

            "sudo" => {
                record_egg("sudo");
                append_terminal_line("jezali is not in the sudoers file. This incident will be reported.");
            }

            "rm" => {
                if trimmed.contains("-rf") {
                    record_egg("rm_rf");
                    append_terminal_line("<span class=\"term-red\">flash erase... aborted: write-protected (RDP level 1).</span>");
                } else {
                    append_terminal_line("rm: missing operand");
                }
            }

            "make" => {
                if args.contains(&"coffee") {
                    record_egg("make_coffee");
                    append_terminal_line("<span class=\"term-yellow\">HTTP/1.1 418 I'm a teapot: RFC 2324 / Embedded boiler unreachable.</span>");
                } else {
                    append_terminal_line("make: *** No targets specified and no makefile found. Stop.");
                }
            }

            "eggs" => {
                let count = get_egg_count();
                append_terminal_line(&format!("Easter eggs discovered: {}/20\nKeep searching terminal commands, avatar interactions, and hardware pinouts.", count));
            }

            _ => {
                append_terminal_line(&format!("command not found: {}. Type 'help' for available commands.", cmd));
            }
        }
    }

    fn handle_vk_answer(&mut self, _answer: &str, step: usize) {
        match step {
            1 => {
                self.vk_step = Some(2);
                append_terminal_line(r#"<span class="term-hl">[PUPIL DILATION: 2.1mm]</span>
Q2: You're watching television. Suddenly you realize there's a wasp crawling on your arm.
(Type your response):"#);
            }
            2 => {
                self.vk_step = Some(3);
                append_terminal_line(r#"<span class="term-hl">[CAPILLARY RESPONSE: NOMINAL]</span>
Q3: You're reading a magazine and come across a full-page color photo of a girl. You show it to your husband. He hangs it on the wall in your bedroom.
(Type your response):"#);
            }
            3 => {
                self.vk_step = None;
                let rand_val = js_sys::Math::random();
                let verdict = if rand_val > 0.4 {
                    "<span class=\"term-aqua\">TEST COMPLETE: HUMAN</span>"
                } else if rand_val > 0.05 {
                    "<span class=\"term-yellow\">TEST COMPLETE: REPLICANT (Nexus-6)</span>"
                } else {
                    "<span class=\"term-red\">TEST COMPLETE: BASELINE ERROR</span>"
                };
                append_terminal_line(&format!("-----------------------------------\n{}\n-----------------------------------", verdict));
            }
            _ => {
                self.vk_step = None;
            }
        }
    }

    pub fn history_prev(&mut self) -> Option<String> {
        if self.history.is_empty() {
            return None;
        }
        if self.history_idx > 0 {
            self.history_idx -= 1;
        }
        self.history.get(self.history_idx).cloned()
    }

    pub fn history_next(&mut self) -> Option<String> {
        if self.history.is_empty() {
            return None;
        }
        if self.history_idx < self.history.len() - 1 {
            self.history_idx += 1;
            self.history.get(self.history_idx).cloned()
        } else {
            self.history_idx = self.history.len();
            Some(String::new())
        }
    }
}

fn append_terminal_line(html: &str) {
    if let Some(out) = get_element_by_id("term-output") {
        let div = document().create_element("div").unwrap();
        div.set_class_name("term-line");
        div.set_inner_html(html);
        let _ = out.append_child(&div);
        out.set_scroll_top(out.scroll_height());
    }
}

fn toggle_theme() {
    let doc_el = document().document_element().unwrap();
    let current = doc_el.get_attribute("data-theme").unwrap_or_default();
    let new_theme = if current == "aqua" { "orange" } else { "aqua" };
    let _ = doc_el.set_attribute("data-theme", new_theme);
    append_terminal_line(&format!("Accent palette switched to: <span class=\"term-hl\">{}</span>", new_theme));
}

fn trigger_lain_cursor() {
    let doc_el = document().document_element().unwrap();
    let _ = doc_el.set_attribute("data-cursor", "wire");
    let win = crate::util::window();
    let cb = Closure::<dyn Fn()>::wrap(Box::new(move || {
        let doc_el = document().document_element().unwrap();
        let _ = doc_el.remove_attribute("data-cursor");
    }));
    let _ = win.set_timeout_with_callback_and_timeout_and_arguments_0(cb.as_ref().unchecked_ref(), 5000);
    cb.forget();
}

pub fn init_terminal(canvas_ref: Rc<RefCell<CanvasState>>) -> Result<(), JsValue> {
    let term_state = Rc::new(RefCell::new(TerminalState::new(canvas_ref)));

    let input_el = match get_element_by_id("term-input") {
        Some(el) => el.dyn_into::<HtmlInputElement>()?,
        None => return Ok(()),
    };

    // Handle keydown on input
    {
        let term_state = Rc::clone(&term_state);
        let input_clone = input_el.clone();
        let on_keydown = Closure::<dyn Fn(KeyboardEvent)>::wrap(Box::new(move |e: KeyboardEvent| {
            let key = e.key();
            match key.as_str() {
                "Enter" => {
                    let val = input_clone.value();
                    input_clone.set_value("");
                    term_state.borrow_mut().execute(&val);
                }
                "ArrowUp" => {
                    e.prevent_default();
                    if let Some(cmd) = term_state.borrow_mut().history_prev() {
                        input_clone.set_value(&cmd);
                    }
                }
                "ArrowDown" => {
                    e.prevent_default();
                    if let Some(cmd) = term_state.borrow_mut().history_next() {
                        input_clone.set_value(&cmd);
                    }
                }
                "Tab" => {
                    e.prevent_default();
                    let current = input_clone.value();
                    let cmds = [
                        "help", "whoami", "whoami --nexus", "ls", "cat about",
                        "projects", "contact", "neofetch", "clear", "theme",
                        "samurai", "afterlife", "johnny", "delamain", "edgerunner",
                        "ghost", "ghost-dive", "tetsuo", "lain", "augment",
                        "vk", "cells", "rain", "la", "eggs", "0xdeadbeef"
                    ];
                    for c in &cmds {
                        if c.starts_with(&current.to_lowercase()) && !current.is_empty() {
                            input_clone.set_value(c);
                            break;
                        }
                    }
                }
                _ => {}
            }
        }));
        let _ = input_el.add_event_listener_with_callback("keydown", on_keydown.as_ref().unchecked_ref());
        on_keydown.forget();
    }

    // Handle suggestion chips clicks
    {
        let doc = document();
        let chips = doc.query_selector_all(".term-chip").unwrap();
        for i in 0..chips.length() {
            if let Some(node) = chips.get(i) {
                if let Ok(el) = node.dyn_into::<web_sys::HtmlElement>() {
                    let term_state = Rc::clone(&term_state);
                    let cmd = el.get_attribute("data-cmd").unwrap_or_default();
                    let on_click = Closure::<dyn Fn(MouseEvent)>::wrap(Box::new(move |_e| {
                        term_state.borrow_mut().execute(&cmd);
                        if let Some(inp) = get_element_by_id("term-input") {
                            let _ = inp.dyn_into::<HtmlInputElement>().map(|i| i.focus());
                        }
                    }));
                    let _ = el.add_event_listener_with_callback("click", on_click.as_ref().unchecked_ref());
                    on_click.forget();
                }
            }
        }
    }

    Ok(())
}
