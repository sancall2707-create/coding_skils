# Design System Implementation Notes

## Brand Tokens
- Background/surface: `#FAF8FF`
- Primary: `#2563EB`
- Amber: `#F59E0B`
- Emerald: `#10B981`
- Rose: `#F43F5E`
- Text: Slate hierarchy (`#0F172A`, `#475569`, `#E2E8F0`)

## Typography
Use Google Fonts in Blade:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
```

Define utility classes in `resources/css/app.css`:
```css
.font-display { font-family: 'Plus Jakarta Sans', ui-sans-serif, system-ui, sans-serif; }
.font-body { font-family: 'Inter', ui-sans-serif, system-ui, sans-serif; }
```

## Student UI
- Use tactile 3D buttons: 52px height, `rounded-full`, bold, `box-shadow: 0 4px 0 #1D4ED8`.
- Active pressed state: `transform: translateY(2px)` and lower shadow.
- Answer pills: min 56px height, rounded-full, selected border `#4F46E5`, correct emerald, incorrect rose + shake.
- Checkpoint roadmap: 64px circular nodes with completed/active/locked states.

## Teacher UI
- Use card surfaces: white, border `#E2E8F0`, rounded-xl.
- Data tables need `min-w-[1100px]` and horizontal scroll to avoid header collision.
- Use score chips:
  - `<60`: Perlu Bimbingan (rose)
  - `60–74`: Cukup (amber)
  - `75–89`: Baik (blue)
  - `90–100`: Sangat Mahir (emerald)

## Common Visual Pitfalls
- Long Indonesian phrases truncate easily; prefer `line-clamp-2` or wrap instead of `truncate` for subtitles.
- Teacher sidebar long names should `truncate` with `title` attribute or wrap in two lines.
- CRUD lists with 24+ cards need search/filter; otherwise dashboard feels broken/overwhelming.