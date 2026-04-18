# A Story of Love and Death — Project Document

Live: https://gabrieletng.github.io/hello-world/

---

## Concept

A photography collection website. Multiple landing pages act as curated "stories" — each with its own text and 12 images from the main collection. Visitors can also explore the full collection via a zoomable canvas or carousel. Social layer: cross-device likes and a profile page, via Google sign-in.

---

## Repo Structure (target)

```
/
├── index.html              ← landing page 1
├── landing/
│   └── [page-name].html   ← additional landing pages
├── explore/
│   ├── grid.html          ← full collection, zoomable/pannable canvas
│   └── carousel.html      ← full collection, one image at a time
├── profile/
│   └── index.html         ← liked images, requires sign-in
├── images/                ← full image collection (WebP, max 1600px, quality 82)
├── manifest.json          ← source of truth: { file, title, date } per image
├── js/
│   ├── marquee.js         ← shared landing page engine
│   └── firebase.js        ← shared auth + Firestore module
└── scripts/
    └── optimize.py        ← local: convert new images to WebP before commit
```

---

## Pages

### Landing pages
- Dual scrolling marquee (top + bottom bands), opposite directions
- Center text (title of the story)
- Each page declares its own text + 12 images drawn from the collection
- All share `js/marquee.js` for the animation/drag engine
- **No like button** on landing pages
- Navigation between landing pages and to explore views: TBD (UX/UI task)

### Grid (`explore/grid.html`)
- Zoomable/pannable infinite canvas — like a digital mood board
- **Dark background**
- Images scattered at varying positions and sizes — no strict columns, no rotation
- "Scattered papers on the floor" feel, but curated/gallery quality
- Zoom out → see full collection from above; zoom in → focus on individual images
- Pan by dragging; zoom by scroll/pinch
- Like button on hover (not on landing pages)
- Lightbox on click: full-screen single image view

### Carousel (`explore/carousel.html`)
- Full collection, one image at a time, full-bleed
- Toggle: random order / chronological (by `date` in manifest)
- Like button visible

### Profile (`profile/index.html`)
- Grid of liked images for the signed-in user
- Requires Google sign-in (Firebase Auth)

---

## Design

### Grid canvas
- Background: near-black (`#0d0d0d` or similar)
- Images placed with pseudo-random layout: cell-based with jitter to distribute evenly but feel organic
- Image sizes vary: roughly 80px–280px display height, maintaining aspect ratio
- No rotation — irregular placement only comes from position and size variation
- Consistent layout seed so the arrangement is the same on every load
- Default zoom: shows most/all of collection; zoom range: ~0.05 (full overview) to ~2.0 (detail)

### General aesthetic
- Clean, minimal UI chrome
- Typography: Bebas Neue (landing pages); system/clean sans elsewhere
- Colors: white background on landing pages, dark on grid/explore

---

## Image Management

### Collection (`images/`)
- All images: WebP format, max 1600px longest side, quality 82 (via `scripts/optimize.py`)
- Naming: lowercase, hyphen-separated, no spaces or special chars, `.webp` extension
- Source of truth: `manifest.json`

### manifest.json format
```json
[
  { "file": "images/camdenthrasher.webp", "title": "Camden Thrasher", "date": "2024-03-10" },
  ...
]
```
- `title` and `date` drive chronological sort and metadata display
- File paths work with both local repo and future CDN (update the path prefix only)
- Many entries currently have `null` title/date — to be filled in over time

### Storage strategy
- Stay in GitHub repo while under ~500MB (currently ~14MB for 170 images)
- Migrate to Bunny.net CDN when needed — only `manifest.json` file paths change

### Adding new images
```bash
python3 scripts/optimize.py /path/to/new/images/
# Then update manifest.json with new entries
```

---

## Social Layer (Phase 3)

- **Firebase Auth**: Google sign-in only, no passwords
- **Firestore**: stores `{ userId, imageFile, likedAt }` per like
- **Like button**: appears on hover in grid and carousel (not on landing pages)
- **Profile page**: reads liked images from Firestore, displays as grid
- **Sharing**: Web Share API (native on mobile), copy-link fallback on desktop

---

## Navigation (TBD — UX/UI task)

How users move between:
- Landing pages (multiple, same structure)
- Grid / Carousel
- Profile

Open questions:
- Minimal floating menu vs. gesture-based transitions
- Entry point: which page is `index.html`?
- How to cycle between landing pages

---

## Development Phases

### Phase 1 — Architecture ✅
- [x] Move images to `images/`, clean filenames
- [x] Extract `js/marquee.js` shared engine
- [x] Refactor `index.html` to use shared module
- [x] Create `manifest.json`
- [x] `scripts/optimize.py` — batch WebP conversion

### Phase 2 — Full Collection (in progress)
- [x] 170 images compressed and added to collection
- [ ] `explore/grid.html` — zoomable/pannable canvas ← current
- [ ] `explore/carousel.html` — random/chronological toggle

### Phase 3 — Social
- [ ] Firebase project setup
- [ ] `js/firebase.js` — auth + Firestore module
- [ ] Like button (grid + carousel)
- [ ] `profile/index.html`

### Phase 4 — Image Pipeline
- [ ] CDN migration path (update manifest paths only)

### Ongoing — Navigation UX/UI
- [ ] Design navigation between landing pages and explore views
- [ ] Implement chosen pattern
