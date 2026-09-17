# janoschbajorath.com — design

Personal academic site: one central place for who Janosch is and what he does. Hub, not archive: every page links out to the original source (poster PDF, arXiv, GitHub, lab page).

## Decisions (2026-09-08 … 2026-09-17)

- Domain `janoschbajorath.com`, registered at Porkbun. Redirects/extra domains later.
- Hosting: GitHub Pages from `TheExplorer95/janoschbajorath.com`, deploy on push to `main` via `withastro/action`. `public/CNAME` carries the domain.
- Tooling: Astro 7, content collections (`research`, `teaching`) from markdown/MDX; MDX for HTML islands when markdown is not enough. Math via remark-math + rehype-katex on the unified processor (Sätteri, Astro 7's default, has no KaTeX rendering). YouTube embeds via `<YouTube id="…" />`. Fira Sans + the poster's green (`#1F9423`) for visual continuity with printed material.
- Content workflow: one markdown file per project or tutorial; index pages generate themselves. Standalone pages (about, cv, statement, teaching intro) are markdown in `src/prose/`.
- CV: PDF is the source of truth (`public/files/janosch-bajorath-cv.pdf`); `/cv` shows a short web version kept in sync by hand.
- Interactive figures: not in the MVP; the page format (MDX) does not block them.
- News/blog: not now.

## Site map

```
/                    landing: name, tagline, portrait, link row, recent research
/about               bio
/cv                  PDF download + short web CV
/research            statement · projects · posters/papers/talks
/research/<id>       project page: eyebrow, title, subtitle, authors, buttons, status notice, body
/teaching            intro · tutorial list
/teaching/<id>       overview + examples → GitHub
/where2026           redirect → /research/where-2026 (printed on the WHERE 2026 poster QR)
```

## Frontmatter

research: `title, subtitle?, summary, authors[], kind (poster|paper|talk|project), venue?, date, status?, links{poster,paper,code,videos,slides,lab}`
teaching: `title, summary, format, date, links{…}`

## Copy rules for WHERE 2026 material (from the poster programme note)

Never: "robustness", "axis", "pillar", the trot-collapse anecdote, the gait-schedule speed-coupling mechanism ("by the environment" only). On the site, not the wall: the five-level adaptivity ladder, the "how these were run" statement.

## Launch checklist

- [ ] Domain bought, DNS: 4 × A records to GitHub Pages IPs + CNAME `www` → `theexplorer95.github.io`
- [ ] GitHub repo created, Pages source = GitHub Actions, custom domain set, HTTPS enforced
- [ ] Portrait, tagline, real links in `src/data/site.ts`
- [ ] CV PDF in `public/files/`
- [ ] WHERE poster PDF in `public/files/` once final, linked from the project page
- [ ] Teaching entries replace the placeholder
