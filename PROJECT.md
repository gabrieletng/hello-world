# A Story of Love and Death — Project Document

Live: https://gabrieletng.github.io/hello-world/

---

## Concept

A photography collection website. Multiple landing pages act as curated "stories" — each with its own text and 12 images from the main collection. Visitors can also explore the full collection via a grid or carousel. Social layer: cross-device likes and a profile page, via Google sign-in.

---

## Repo Structure (target)

```
/
├── index.html              ← landing page 1
├── landing/
│   └── [page-name].html   ← additional landing pages
├── explore/
│   ├── grid.html          ← full collection, masonry/irregular layout
│   └── carousel.html      ← full collection, one image at a time
├── profile/
│   └── index.html         ← liked images, requires sign-in
├── images/                ← full image collection (WebP, ~400px height)
├── manifest.json          ← source of truth: { file, title, date } per image
├── js/
│   ├── marquee.js         ← shared landing page engine
│   └── firebase.js        ← shared auth + Firestore module
└── scripts/
    └── optimize.sh        ← local: convert new images to WebP before commit
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
- Full collection, irregular masonry layout
- No image rotation — "curated mess" feel, not chaotic
- Pan/scroll freely
- Click image → full-screen lightbox
- Like button on hover

### Carousel (`explore/carousel.html`)
- Full collection, one image at a time, full-bleed
- Toggle: random order / chronological (by `date` in manifest)
- Like button visible

### Profile (`profile/index.html`)
- Grid of liked images for the signed-in user
- Requires Google sign-in (Firebase Auth)

---

## Image Management

### Collection (`images/`)
- All images live here: WebP format, ~400px height target
- Naming: lowercase, hyphen-separated, no spaces or special chars
- Source of truth: `manifest.json`

### manifest.json format
```json
[
  { "file": "images/camdenthrasher.png", "title": "Camden Thrasher", "date": "2024-03-10" },
  ...
]
```
- `title` and `date` drive chronological sort in carousel and metadata display
- `file` paths work with both local repo and future CDN (just update the path prefix)

### Storage strategy
- Stay in GitHub repo while collection is under ~500MB (optimized)
- Migrate to Bunny.net CDN when needed — only `manifest.json` file paths change

### Image optimization (before committing new images)
Run `scripts/optimize.sh` to convert and resize to WebP. TBD.

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

Options to explore:
- Minimal nav bar or floating menu
- Gesture/scroll-based transitions between landing pages
- Entry point: which page is the default `index.html`?

---

## Development Phases

### Phase 1 — Architecture ✅ (in progress)
- [x] Move images to `images/`, clean up filenames
- [ ] Extract `js/marquee.js` shared engine
- [ ] Refactor `index.html` to use shared module
- [ ] Create `manifest.json` for current 12 images

### Phase 2 — Full Collection
- [ ] `explore/grid.html` — irregular masonry, pan/scroll, lightbox
- [ ] `explore/carousel.html` — random/chronological toggle

### Phase 3 — Social
- [ ] Firebase project setup
- [ ] `js/firebase.js` — auth + Firestore module
- [ ] Like button (grid + carousel)
- [ ] `profile/index.html`

### Phase 4 — Image Pipeline
- [ ] `scripts/optimize.sh` — batch WebP conversion + resize
- [ ] CDN migration path (update manifest paths only)

### Ongoing — Navigation UX/UI
- [ ] Design navigation between landing pages and explore views
- [ ] Implement chosen pattern
