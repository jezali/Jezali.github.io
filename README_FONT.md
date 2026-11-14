# Self-Hosted Font Subsetting Guide

This project uses **IBM Plex Mono** (Regular weight, Latin character set), self-hosted in `fonts/ibm-plex-mono.woff2` (14.7 KB).

To generate or re-subset a font from source TTF/OTF files with `fonttools`:

### 1. Install fonttools & brotli
```bash
pip install fonttools brotli
```

### 2. Subset to Latin Basic + Engineering Glyphs
```bash
pyftsubset IBMPlexMono-Regular.ttf \
  --output-file=fonts/ibm-plex-mono.woff2 \
  --flavor=woff2 \
  --layout-features='*' \
  --unicodes="U+0020-007E,U+00A0-00FF,U+2190-2193,U+2500-257F,U+2580-259F,U+263C,U+2605,U+263D,U+03A9,U+00B1"
```

### Unicode Ranges Included:
- `U+0020-007E`: Basic Latin (ASCII)
- `U+00A0-00FF`: Latin-1 Supplement
- `U+2190-2193`: Arrows (← ↑ → ↓)
- `U+2500-257F`: Box drawing characters (─ │ ┌ ┐ etc.)
- `U+2580-259F`: Block elements (█ ░ ▒ etc. for terminal ASCII meters)
- `U+03A9`: Ohm symbol (Ω for resistor values)
- `U+00B1`: Plus-minus sign (±)
- `U+2605`: Star (★ for GitHub stars)
- `U+263D`: Moon (☾ for cyberpsychosis meter completion)
