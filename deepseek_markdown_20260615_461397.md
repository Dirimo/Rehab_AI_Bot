# ChatTide — "Chat IA en ligne" Design Spec

A design reference distilled from `https://www.chattide.ai/fr/ai-chat/`. Use this to
recreate the same look & feel. It is a single full-viewport hero centered on a chat
input, sitting on a soft cream→sky-blue gradient with layered "wave/blur" background art.

---

## 1. Overall Layout

- **Full-bleed hero** that fills 100vh. Content is absolutely centered.
- **Fixed top bar** (transparent) spanning the full width.
- **Vertical stack, centered:** mascot/logo glyph → H1 → chat input card.
- A small **chevron-down** sits at the bottom center hinting at more sections below
  (additional marketing sections: "Créez tout type de contenu…", "Posez vos questions à l'IA…",
  "Apprenez et trouvez de nouvelles idées…", plus a footer with legal links).
- Max content width for the centered block is **~720px**; the H1 block sits around **27%** from the top.

```
┌───────────────────────────────────────────────┐
│ [◐ ChatTide]      Chat IA  ChatGPT gratuit      [⬆ Mettre à niveau] [user] │
│                                                 │
│                     (mascot glyph)              │
│                  Chat IA en ligne   (H1)        │
│        ┌─────────────────────────────────┐     │
│        │ 🧩 Aidez-moi avec ce problème…  │     │
│        │ [🖼]                       ( ↑ ) │     │
│        └─────────────────────────────────┘     │
│                        ⌄                        │
└───────────────────────────────────────────────┘
```

---

## 2. Color Palette

Light theme only. Text is near-black; the brand warmth comes from the layered background.

| Token            | Value                          | Usage                              |
|------------------|--------------------------------|------------------------------------|
| Background base  | `rgb(248, 247, 247)` (#F8F7F7) | Page body background               |
| Foreground/Text  | `#0A0A0A` (rgb 10,10,10)       | Headings, nav links, body text     |
| Cream accent     | `#FFF1E3` (rgb 255,241,227)    | Warm top-left of gradient          |
| Pure white       | `#FFFFFF`                      | Gradient start, input card, glow   |
| Sky blue (art)   | `~#BBD9F5 → #DDEBFB`           | Bottom wave imagery                |
| Hairline border  | `rgba(10,10,10,0.12)`          | Pill button border                 |
| Card shadow      | `rgba(10,10,10,0.08)`          | Soft drop shadow on input + cards  |

> Keep it to these few colors. No purple. The blue is decorative (background art), not a
> UI accent — interactive text stays near-black.

---

## 3. Background Composition (the signature look)

The hero background is built from **stacked absolutely-positioned layers** (`inset-0`),
each on its own negative z-index, from back to front:

1. **Base gradient** (`-z-10`): warm horizontal gradient
   ```css
   background-image: linear-gradient(90deg, #FFFFFF 0%, #FFF1E3 15.51%);
   ```
   Net effect across the page: cream at the top-left fading to soft sky-blue toward the
   right/bottom.
2. **Shape art** (`-z-9`): a wide decorative webp (`1st_font_shape`), `min-width: 2560px`,
   horizontally centered (`left-1/2 -translate-x-1/2`).
3. **White glow ellipse** (`-z-8`): `width 972px × height 525px`, `border-radius: 50%`,
   `background: #fff; opacity: .8`, centered — creates a bright halo behind the headline.
4. **Blur art** (`-z-6`): a soft blurred blue wave webp (`1st_blur`), also `min-width: 2560px`, centered.

To recreate **without the proprietary images**, approximate with CSS:
```css
.hero {
  position: relative;
  background:
    radial-gradient(60% 50% at 50% 38%, rgba(255,255,255,0.85), transparent 70%),
    linear-gradient(180deg, #FFF7EE 0%, #EAF2FC 55%, #CFE3F8 100%);
}
```
Add a soft blue "wave" blob near the bottom (blurred, low opacity) for the tide motif.

---

## 4. Typography

- **Headings:** `Montserrat` (with fallback). H1 uses **weight 500** (medium, not bold).
- **Body / UI:** system sans stack — `ui-sans-serif, system-ui, sans-serif, …` (no custom body font).
- **H1 ("Chat IA en ligne"):**
  - `font-family: Montserrat`
  - `font-size: 40px` (≈ `text-4xl`)
  - `font-weight: 500`
  - `color: #0A0A0A`
  - `letter-spacing: normal`, centered
- **Section H2s:** Montserrat, medium weight, centered, larger on desktop.
- Body text uses `line-height` ~1.5.

Next.js setup:
```ts
import { Montserrat } from "next/font/google"
const montserrat = Montserrat({ subsets: ["latin"], weight: ["400","500","600"] })
// apply font-sans / a heading class using Montserrat
```

---

## 5. Top Navigation Bar

- Transparent background (`backgroundColor: transparent`), sits over the hero.
- **Left:** circular split logo glyph (◐) + wordmark **"ChatTide"** (Montserrat, ~bold, #0A0A0A).
- **Center:** text links — **"Chat IA"** (active, bold) and **"ChatGPT gratuit"** (regular).
  Link color `#0A0A0A`.
- **Right:**
  - **"Mettre à niveau"** pill button with a small upgrade icon:
    - `background: rgba(255,255,255,0.15)` (frosted)
    - `border: 1px solid rgba(10,10,10,0.12)`
    - `border-radius: 26px` (full pill)
    - `color: #0A0A0A`
    - small padding, icon + label
  - **User/account** icon button.

---

## 6. Chat Input Card (focal element)

- White rounded card, generously padded, centered, `max-width ~720px`.
  - `background: #FFFFFF`
  - `border-radius: 16px`
  - `box-shadow: 0 8px 20px -4px rgba(10,10,10,0.08)` (soft, diffuse)
  - effectively borderless (`border: 0`, hairline color `rgba(10,10,10,0.08)`)
- **Top row:** large placeholder text with a leading emoji, e.g.
  `🧩 Aidez-moi avec ce problème…` / `📝 Faites-moi un résumé de…`
  (placeholder rotates between prompt examples). Muted gray placeholder color.
- **Bottom row:**
  - **Left:** an image/attachment icon button (outline image-plus icon).
  - **Right:** circular **send** button with an up-arrow (↑). Disabled/idle state is a
    muted gray circle; becomes active/colored when text is entered.

---

## 7. Spacing & Shape Language

- **Rounding:** inputs/cards `16px`; pills `full` (`border-radius: 26px`/9999px).
- **Shadows:** always soft, low-opacity, large-blur, slightly raised
  (`0 8px 20px -4px rgba(10,10,10,0.08)`). No harsh borders.
- **Generous whitespace** — the hero is mostly empty space framing the single input.
- Centered alignment for the whole hero stack.
- Mobile: nav center links hide (`max-md:hidden`); logo aligns left; content keeps `px-4` gutters.

---

## 8. Imagery

- A small **mascot/brand glyph** above the H1: a blue chat-bubble with an orbiting ring +
  sparkles (yellow/blue accents). Replace with your own simple branded glyph if recreating.
- Background "wave/tide" art is **decorative only** — safe to approximate with CSS gradients
  + a blurred blue blob (see §3).

---

## 9. Quick Recreation Checklist

- [ ] Full-viewport hero, content absolutely centered, H1 block ~27% from top.
- [ ] Layered background: warm cream→sky-blue gradient + white glow ellipse + soft blue wave.
- [ ] Transparent top bar: logo+wordmark left, two text links center, frosted pill + user icon right.
- [ ] Montserrat for headings (H1 = 40px / weight 500, color #0A0A0A); system sans for body.
- [ ] White chat card: `radius 16px`, soft shadow, emoji placeholder, attach icon (left), round send arrow (right).
- [ ] Pills fully rounded (26px) with `1px rgba(10,10,10,0.12)` border, frosted white bg.
- [ ] Chevron-down at bottom center hinting at scroll sections below.
- [ ] Palette limited to white / cream `#FFF1E3` / base `#F8F7F7` / text `#0A0A0A` / decorative sky-blue.