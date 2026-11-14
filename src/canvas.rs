use wasm_bindgen::prelude::*;
use web_sys::{CanvasRenderingContext2d, HtmlCanvasElement};
use std::cell::RefCell;
use std::rc::Rc;
use crate::util::{window, get_element_by_id, is_fx_enabled};

#[derive(Clone, Copy)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

#[derive(Clone)]
pub struct TraceSegment {
    pub start: Point,
    pub end: Point,
}

#[derive(Clone)]
pub struct SignalPulse {
    pub segment_idx: usize,
    pub progress: f64, // 0.0 to 1.0
    pub speed: f64,
    pub color_aqua: bool,
}

#[derive(Clone)]
pub struct RainDrop {
    pub x: f64,
    pub y: f64,
    pub speed: f64,
    pub len: f64,
}

#[derive(Clone)]
pub struct KatakanaGlyph {
    pub x: f64,
    pub y: f64,
    pub speed: f64,
    pub char_code: char,
}

pub struct CanvasState {
    canvas: HtmlCanvasElement,
    ctx: CanvasRenderingContext2d,
    width: f64,
    height: f64,
    dpr: f64,
    traces: Vec<TraceSegment>,
    vias: Vec<Point>,
    pulses: Vec<SignalPulse>,
    raindrops: Vec<RainDrop>,
    katakana: Vec<KatakanaGlyph>,
    pub rain_active: bool,
    pub ghost_dive_active: bool,
    last_frame_ms: f64,
    pub is_visible: bool,
}

impl CanvasState {
    pub fn new(canvas: HtmlCanvasElement) -> Result<Self, JsValue> {
        let ctx = canvas
            .get_context("2d")?
            .expect("2d context not available")
            .dyn_into::<CanvasRenderingContext2d>()?;

        let mut state = Self {
            canvas,
            ctx,
            width: 0.0,
            height: 0.0,
            dpr: 1.0,
            traces: Vec::new(),
            vias: Vec::new(),
            pulses: Vec::new(),
            raindrops: Vec::new(),
            katakana: Vec::new(),
            rain_active: false,
            ghost_dive_active: false,
            last_frame_ms: 0.0,
            is_visible: true,
        };

        state.resize();
        state.rebuild_traces();
        Ok(state)
    }

    pub fn resize(&mut self) {
        let win = window();
        let w = win.inner_width().ok().and_then(|v| v.as_f64()).unwrap_or(800.0);
        let h = win.inner_height().ok().and_then(|v| v.as_f64()).unwrap_or(600.0);
        let raw_dpr = win.device_pixel_ratio();
        let dpr = raw_dpr.min(1.5).max(1.0);

        self.width = w;
        self.height = h;
        self.dpr = dpr;

        self.canvas.set_width((w * dpr) as u32);
        self.canvas.set_height((h * dpr) as u32);
        let _ = self.ctx.scale(dpr, dpr);
    }

    pub fn rebuild_traces(&mut self) {
        self.traces.clear();
        self.vias.clear();
        self.pulses.clear();
        self.raindrops.clear();
        self.katakana.clear();

        let w = self.width;
        let h = self.height;
        if w <= 10.0 || h <= 10.0 {
            return;
        }

        let trace_count = ((w / 200.0) as usize).clamp(4, 12);
        for i in 0..trace_count {
            let seed_y = ((i as f64 + 0.5) / trace_count as f64) * h;
            let start_x = 0.0;
            let break_x1 = w * 0.25 + ((i * 37) % 80) as f64;
            let break_y1 = seed_y;
            let break_x2 = break_x1 + 60.0;
            let break_y2 = (seed_y + 60.0).min(h - 20.0);
            let end_x = w;
            let end_y = break_y2;

            let p0 = Point { x: start_x, y: seed_y };
            let p1 = Point { x: break_x1, y: break_y1 };
            let p2 = Point { x: break_x2, y: break_y2 };
            let p3 = Point { x: end_x, y: end_y };

            let idx = self.traces.len();
            self.traces.push(TraceSegment { start: p0, end: p1 });
            self.traces.push(TraceSegment { start: p1, end: p2 });
            self.traces.push(TraceSegment { start: p2, end: p3 });

            self.vias.push(p1);
            self.vias.push(p2);

            self.pulses.push(SignalPulse {
                segment_idx: idx,
                progress: (i as f64 * 0.3) % 1.0,
                speed: 0.003 + (i as f64 * 0.001),
                color_aqua: i % 2 == 0,
            });
        }

        // Initialize sparse rain drops buffer (15 drops max)
        for i in 0..15 {
            self.raindrops.push(RainDrop {
                x: ((i * 97) as f64) % w,
                y: ((i * 131) as f64) % h,
                speed: 4.0 + (i % 3) as f64,
                len: 12.0 + (i % 5) as f64 * 3.0,
            });
        }

        // Initialize sparse katakana buffer (8 glyphs)
        let glyphs = ['ア', 'カ', 'サ', 'タ', 'ナ', 'ハ', 'マ', 'ヤ', 'ラ', 'ワ'];
        for i in 0..8 {
            self.katakana.push(KatakanaGlyph {
                x: ((i * 153) as f64) % w,
                y: ((i * 89) as f64) % h,
                speed: 1.5 + (i % 2) as f64,
                char_code: glyphs[i % glyphs.len()],
            });
        }
    }

    pub fn draw(&mut self, timestamp: f64) {
        if !self.is_visible {
            return;
        }

        // Frame rate limiter (~30 FPS: ~33ms interval)
        if timestamp - self.last_frame_ms < 32.0 {
            return;
        }
        self.last_frame_ms = timestamp;

        let w = self.width;
        let h = self.height;

        // Clear canvas
        self.ctx.clear_rect(0.0, 0.0, w, h);

        // Draw traces (static lines in --bg2 #504945)
        self.ctx.set_stroke_style_str("#504945");
        self.ctx.set_line_width(1.0);
        self.ctx.begin_path();
        for trace in &self.traces {
            self.ctx.move_to(trace.start.x, trace.start.y);
            self.ctx.line_to(trace.end.x, trace.end.y);
        }
        self.ctx.stroke();

        // Draw vias (small pads)
        self.ctx.set_fill_style_str("#1d2021");
        for via in &self.vias {
            self.ctx.begin_path();
            let _ = self.ctx.arc(via.x, via.y, 2.5, 0.0, std::f64::consts::PI * 2.0);
            self.ctx.fill();
            self.ctx.stroke();
        }

        if !is_fx_enabled() {
            return;
        }

        // Draw and update signal pulses
        for pulse in &mut self.pulses {
            pulse.progress += pulse.speed;
            if pulse.progress > 1.0 {
                pulse.progress = 0.0;
                pulse.segment_idx = (pulse.segment_idx + 1) % self.traces.len();
            }

            if let Some(trace) = self.traces.get(pulse.segment_idx) {
                let px = trace.start.x + (trace.end.x - trace.start.x) * pulse.progress;
                let py = trace.start.y + (trace.end.y - trace.start.y) * pulse.progress;

                let color = if pulse.color_aqua { "#8ec07c" } else { "#fabd2f" };
                self.ctx.set_fill_style_str(color);
                self.ctx.begin_path();
                let _ = self.ctx.arc(px, py, 2.0, 0.0, std::f64::consts::PI * 2.0);
                self.ctx.fill();
            }
        }

        // Draw sparse pixel rain if active
        if self.rain_active {
            self.ctx.set_stroke_style_str("#83a598");
            self.ctx.set_line_width(1.0);
            self.ctx.begin_path();
            for drop in &mut self.raindrops {
                drop.y += drop.speed;
                if drop.y > h {
                    drop.y = -drop.len;
                    drop.x = (drop.x + 83.0) % w;
                }
                self.ctx.move_to(drop.x, drop.y);
                self.ctx.line_to(drop.x, drop.y + drop.len);
            }
            self.ctx.stroke();
        }

        // Draw sparse ghost-dive katakana if active
        if self.ghost_dive_active {
            self.ctx.set_fill_style_str("#8ec07c");
            self.ctx.set_font("12px monospace");
            for k in &mut self.katakana {
                k.y += k.speed;
                if k.y > h {
                    k.y = 0.0;
                    k.x = (k.x + 97.0) % w;
                }
                let mut buf = [0u8; 4];
                let s = k.char_code.encode_utf8(&mut buf);
                let _ = self.ctx.fill_text(s, k.x, k.y);
            }
        }
    }
}

pub fn init_canvas() -> Result<Rc<RefCell<CanvasState>>, JsValue> {
    let canvas = get_element_by_id("pcb-canvas")
        .expect("missing #pcb-canvas")
        .dyn_into::<HtmlCanvasElement>()?;

    let state = Rc::new(RefCell::new(CanvasState::new(canvas)?));

    // Handle window resize
    {
        let state = Rc::clone(&state);
        let on_resize = Closure::<dyn Fn()>::wrap(Box::new(move || {
            let mut s = state.borrow_mut();
            s.resize();
            s.rebuild_traces();
        }));
        let _ = window().add_event_listener_with_callback("resize", on_resize.as_ref().unchecked_ref());
        on_resize.forget();
    }

    // Handle tab visibility change
    {
        let state = Rc::clone(&state);
        let on_vis = Closure::<dyn Fn()>::wrap(Box::new(move || {
            let doc = crate::util::document();
            let hidden = doc.hidden();
            state.borrow_mut().is_visible = !hidden;
        }));
        let _ = crate::util::document().add_event_listener_with_callback("visibilitychange", on_vis.as_ref().unchecked_ref());
        on_vis.forget();
    }

    // Animation frame loop
    {
        let state = Rc::clone(&state);
        let f: Rc<RefCell<Option<Closure<dyn FnMut(f64)>>>> = Rc::new(RefCell::new(None));
        let g = Rc::clone(&f);

        *g.borrow_mut() = Some(Closure::wrap(Box::new(move |timestamp: f64| {
            state.borrow_mut().draw(timestamp);
            if let Some(ref cb) = *f.borrow() {
                let _ = window().request_animation_frame(cb.as_ref().unchecked_ref());
            }
        }) as Box<dyn FnMut(f64)>));

        let _ = window().request_animation_frame(
            g.borrow()
                .as_ref()
                .unwrap()
                .as_ref()
                .unchecked_ref(),
        );
    }

    Ok(state)
}
