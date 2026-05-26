# jasonead.com Rebuild – Chief-of-Staff Planning Document

**Date:** 2026-05-02  
**Status:** Planning Phase (no agents spawned)  
**Project Manager:** chief-of-staff (acting as project manager per current allowlist)  

---

## Verdict: Recommended Site Type

**Blunt recommendation:** Build a **full personal brand site with business‑focused portfolio elements**, not a simple static landing page, and not an over‑the‑top 3D experience.  

Why:  
- Jason’s goals (systems engineer, automation, AI‑workflow builder) need more than a one‑page pitch.  
- A full site lets you showcase services, case studies (anonymized), about, and contact.  
- A **tasteful, performance‑first 3D hero** can reinforce the “systems/automation” brand without hurting Core Web Vitals.  
- Skip the “advanced animated/3D web experience” route – it risks performance, accessibility, and maintenance overhead.

---

## 1. Current Understanding of the Website Goal

Replace the existing jasonead.com with a sleek, modern, high‑quality personal‑brand and services site that positions Jason as a systems engineer, automation specialist, AI‑workflow builder, and operational problem‑solver. The site must feel premium, technical, and conversion‑ready, while staying fast and accessible.

## 2. Assumptions

- You want a professional site that can evolve into a hub for your projects, writing, and future products.  
- You prefer a dark‑mode‑first aesthetic with a technical, “engineered” vibe.  
- You will provide copy, brand assets (logo, photo), and any case‑study material you want included.  
- Hosting on Vercel/Netlify is acceptable; DNS management is under your control.  
- n8n or a simple form endpoint will handle contact inquiries.  
- 3D hero is desirable but must be lightweight and have a static fallback.  

## 3. Target Audience

| Audience | What they need to see |
|----------|-----------------------|
| Potential clients (CTOs, founders, ops leads) | Clear services, measurable outcomes, credibility |
| Employers (tech leadership) | Technical depth, systems thinking, stack familiarity |
| Collaborators / open‑source community | Projects, writing, automation experiments |
| Potential leads (automation seekers) | Quick value proposition, easy contact path |

## 4. Brand Positioning

**Core positioning:** “I engineer the invisible pipelines that let businesses scale without chaos.”  

**Tone:** Direct, competent, under‑stated confidence. No marketing fluff.  

**Key differentiators:**  
- Real‑world systems engineering background.  
- Hands‑on automation (n8n, Docker, OpenClaw).  
- AI‑workflow integration expertise.  
- Operational problem‑solving that delivers measurable efficiency gains.

## 5. Recommended Website Purpose

- Present Jason’s professional identity and services.  
- Convert visitors into leads (consulting, automation audit, project work).  
- Provide a hub for writing, case studies, and future product launches.  
- Demonstrate technical competence through a polished, fast, accessible experience.

## 6. Site Map

1. **Home** – Hero, services overview, about snippet, social proof, CTA.  
2. **Services** – Detailed pages/sections for each core service.  
3. **About** – Bio, philosophy, tech stack, selected projects.  
4. **Work / Case Studies** (optional) – 2‑3 anonymized examples of systems built.  
5. **Contact** – Form, calendar link, email, social icons.  
6. **Legal** – Privacy policy, terms (static).  

## 7. Homepage Section Outline

| # | Section | Purpose | Key Elements |
|---|----------|----------|---------------|
| 1 | **Hero with 3D Background** | Immediate positioning + visual hook | Headline, subhead, primary CTA, floating nodes animation |
| 2 | **Services Grid** | Quick‑scan of core offers | 3‑4 cards with icon, title, one‑sentence value prop |
| 3 | **About Snippet** | Humanize, build trust | Photo/avatar, short bio, “my approach” bullets |
| 4 | **Social Proof / Logos** (if available) | Credibility | Tool logos (AWS, Docker, n8n, OpenClaw) |
| 5 | **Process / Methodology** | Show systems thinking | 3‑step visual: Audit → Automate → Scale |
| 6 | **Secondary CTA** | Capture leads lower in page | “Get an automation audit” button |
| 7 | **Footer** | Navigation, contact, legal | Links, email, calendar, social icons |

## 8. Visual Direction

**Color palette**  
- Primary dark: `#0f172a` (deep navy‑slate)  
- Accent: `#22d3ee` (bright cyan) – for CTAs, glowing lines  
- Neutral light: `#f8fafc` – text on dark, card backgrounds  
- Text on dark: `#e2e8f0`  
- Success/graph: `#10b981`  

**Typography**  
- Headings: `Inter` (or `Geist Sans`) – bold, tight line‑height.  
- Body: `Inter` – regular weight, 1.6 line‑height.  
- Monospace (code, system snippets): `JetBrains Mono`.  

**Layout**  
- Max‑width `1200px`, centered, generous padding (`px‑6`).  
- Cards: `rounded‑2xl`, subtle `shadow‑lg`.  
- Spacing: 8‑point grid (8, 16, 24, 32, 48, 64).  

**Motion**  
- Use `framer‑motion` for subtle fade‑in, slide‑up on scroll (≤ 0.4 s).  
- Disable all non‑essential animation when `prefers‑reduced‑motion` is set.  

**Components**  
- Buttons: `px‑6 py‑3 rounded‑full`, accent background, hover scale.  
- Inputs: `focus:ring‑cyan‑500`.  
- Icons: Lucide React (outline style).  

**Overall aesthetic:** Dark‑mode‑first, high contrast, “technical dashboard” vibe without clutter.

## 9. 3D / Animated Hero Concept

**Concept:** A stylized “automation pipeline” – floating, translucent geometric nodes (cubes/spheres) connected by glowing lines that pulse, representing data flowing through a system.  

**Interaction:** Subtle mouse‑parallax (nodes move slightly with cursor). No click‑through.  

**Technical approach:**  
- React Three Fiber (R3F) + Three.js.  
- Load a single low‑poly GLTF scene (Draco‑compressed).  
- Animate node emissive intensity via `sin(time)`.  
- Use `Float` component from `@react‑three/drei` for gentle hover.  

**Fallback state:** Static high‑res screenshot of the 3D scene, served as `<picture>` with WebP + PNG. Detect WebGL support or `prefers‑reduced‑motion`.  

**Performance guardrails:**  
- Max polygons: 50k.  
- Frame‑rate cap on mobile: 30 fps (throttle via `useFrame` delta).  
- Disable animation when `prefers‑reduced‑motion` is set.  
- Use `Suspense` + `fallback` to avoid blocking page load.  
- No physics engines; keep math simple.  

## 10. Suggested Tech Stack

| Layer | Tool / Framework | Reason |
|-------|-------------------|--------|
| Frontend | **React + Vite** (or Next.js if SEO‑heavy) | Fast builds, modern DX |
| Styling | **Tailwind CSS** + custom design tokens | Rapid, consistent UI |
| 3D / Animation | **React Three Fiber + Three.js** | Declarative 3D in React |
| 3D Assets | GLTF/GLB low‑poly, Draco‑compressed | Performance‑first |
| State | **Zustand** (or React context) | Lightweight |
| Forms | **React Hook Form + Formspree / n8n webhook** | No backend initially |
| Analytics | **Plausible** (or Simple Analytics) | Privacy‑friendly |
| Hosting | **Vercel** (or Netlify) | CI/CD, edge rendering |
| CMS (optional) | **Sanity (headless)** or markdown files | If content changes often |
| Automation | **n8n** (self‑hosted or cloud) | Form → CRM/email workflows |

## 11. Copy Direction (samples)

**Hero headline**  
`Systems engineered. Workflows automated.`

**Hero subheadline**  
`I design and build the invisible pipelines that let businesses scale without the chaos.`

**Primary CTA button**  
`Book an automation audit`

**Secondary CTA (lower page)**  
`Get a free workflow assessment`

**Services section – card titles & one‑liners**  
- **Automation Architecture** – “Replace manual steps with reliable, self‑healing pipelines.”  
- **AI‑Workflow Integration** – “Connect LLMs, APIs, and your stack into one coordinated system.”  
- **Systems Engineering** – “Design the backbone that keeps your ops lean and observable.”  
- **Operational Problem‑Solving** – “Identify bottlenecks, then dismantle them with precision.”

**About section snippet**  
`I’m Jason—a systems engineer who treats business operations like software: measured, iterable, and built to last. My background spans automation, AI‑tooling, and the kind of hands‑on debugging that keeps teams moving.`

**Footer CTA**  
`Ready to streamline?` [Email icon] `jason@jasonead.com` | [Calendar icon] `Book a call`

## 12. Content Needed from Jason

- Logo / brand mark (or approval to create a simple word‑mark).  
- Professional photo or avatar.  
- Finalized copy for all pages (or approval of the samples above).  
- Any case‑study details you want to include (anonymized).  
- Preferred contact email, calendar link, social URLs.  
- Hosting and DNS access (if not already available).  
- Analytics account ID (Plausible, etc.).  
- Preferred form backend (Formspree, n8n, custom).

## 13. Risks and Open Questions

- **Brand assets:** No logo yet – need to decide on creation or temporary text‑only brand.  
- **Hosting choice:** Vercel vs Netlify vs self‑hosted? Who controls DNS?  
- **CMS need:** Will you update content often? If yes, approve Sanity or similar.  
- **Analytics:** Which privacy‑friendly analytics do you prefer?  
- **Contact form backend:** Formspree (quick) vs n8n webhook (more control).  
- **Release scope:** MVP first (home + contact) or full site before launch?  
- **3D asset creation:** Who will model the low‑poly scene? Need Blender or outsourced?  
- **Legal pages:** Need templates for privacy policy/terms?  

## 14. Single‑Agent Execution Plan (chief‑of‑staff only)

Since only `chief-of-staff` can be spawned, this phase is executed directly:

1. **Finalize brand & copy** – approve or adjust the samples above.  
2. **Choose tech stack** – confirm React+Vite, Tailwind, R3F, etc.  
3. **Create design tokens** – generate Tailwind config with the color palette, typography, spacing.  
4. **Scaffold project** – run `npm create vite@latest jasonead-site – –template react`.  
5. **Implement layout & routing** – set up React Router, responsive shell, dark mode toggle.  
6. **Build components** – hero, services cards, about section, footer, etc.  
7. **Integrate 3D hero** – model/export GLTF, build R3F scene, add fallback.  
8. **Add copy & images** – insert finalized text, optimize images (WebP).  
9. **Set up forms & analytics** – wire contact form to endpoint, add Plausible snippet.  
10. **Test & audit** – Lighthouse, a11y, cross‑browser, form submission.  
11. **Deploy** – connect repo to Vercel, configure env vars, update DNS.  

All steps will be presented as **Ready to run** or **Ready to paste** blocks, with approval gates before any file changes or command execution.

## 15. Future Specialist‑Agent Delegation Plan (once allowlist expanded)

When `sessions_spawn` permits additional agentIds, the work will be re‑organized as follows:

| Specialist agent (file) | Role | What they would contribute |
|--------------------------|------|---------------------------|
| `project-management-project-shepherd` | Project manager | Detailed timeline, dependency map, risk register, stakeholder updates |
| `design-ux-architect` | UX/UI foundation | Wireframes, user‑flow diagrams, responsive breakpoints, component hierarchy |
| `design-brand-guardian` | Brand identity | Finalized color palette, typography scale, logo concepts, style tile |
| `design-ui-designer` | UI implementation plan | Component breakdown, state‑management plan, R3F integration points |
| `marketing-seo-specialist` | SEO strategy | Keyword research, title/meta templates, schema JSON‑LD, Open Graph tags |
| `marketing-content-creator` | Copywriting | Polished copy for all pages, blog posts if needed, CTA variants |
| `specialized-model-qa` | QA/audit | Performance budget, accessibility checklist, security headers, testing plan |

Each agent would be spawned with isolated context, would deliver its output, and would end with the required handoff line. The chief‑of‑staff would then review, merge, and present the unified plan.

## 16. Agent Enablement Plan (what must change to allow specialist spawning)

1. **Locate the allowlist** – inspect the OpenClaw gateway configuration:  
   ```bash
   # Ready to run (inspection only)
   grep -R "allowedAgents\|spawnAllowlist\|agentIdWhitelist" /home/openclaw/.openclaw/gateway/ 2>/dev/null
   ```  
   The relevant file is likely `/home/openclaw/.openclaw/gateway/configuration.yaml` (or `config.json`).  

2. **Review current entries** – find the key that lists permitted `agentId` values. It probably contains only `chief-of-staff`.  

3. **Proposed change** – add the required agent IDs to that list:  
   ```yaml
   # Example snippet (exact syntax depends on config structure)
   sessionsSpawnAllowlist:
     - chief-of-staff
     - project-management-project-shepherd
     - design-ux-architect
     - design-brand-guardian
     - design-ui-designer
     - marketing-seo-specialist
     - marketing-content-creator
     - specialized-model-qa
   ```  

4. **Safety/rollback** – backup the config before editing:  
   ```bash
   # Ready to run (after approval)
   cp /home/openclaw/.openclaw/gateway/configuration.yaml \
      /home/openclaw/.openclaw/gateway/configuration.yaml.bak_$(date +%Y%m%d_%H%M%S)
   ```  

5. **Apply change** – edit the file (or use `gateway` tool action `config.patch`).  

6. **Restart gateway** – `openclaw gateway restart` (or the appropriate service restart).  

7. **Validate** – test `sessions_spawn` with one of the new agentIds to confirm it no longer returns “agentId is not allowed”.  

8. **Approval gate** – **you must approve** each of the following before they happen:  
   - Inspection of the gateway config file.  
   - Any edit to the allowlist.  
   - Gateway restart.  
   - Testing of a new agentId.  

---

**Next action for you:**  
Approve one of the following:  

- **A.** Approve **config inspection only** – I will give you the exact command to view the allowlist.  
- **B.** Approve **full enablement** – inspection + editing + restart after your explicit “approve” for each step.  
- **C.** **Continue with chief‑of‑staff only** – proceed to implement the single‑agent execution plan, deferring agent enablement.  

I will not perform any of these without your explicit approval.
