# Intaaneto minimal design system

Use this reference as a decision aid, not as permission for a broad redesign.
Prefer existing tokens and primitives when they already meet these constraints.

## Current frontend facts

- Runtime: React 18 with Vite.
- Styling: Tailwind CSS plus shared styles in `frontend/src/index.css`.
- Routing: React Router.
- Icons: Lucide React and Heroicons are installed; prefer Lucide for new work.
- Motion: Framer Motion is installed but optional. CSS transitions are enough for
  most state feedback.
- Shared UI exists under `frontend/src/components/ui`; inspect before adding a
  new primitive.

The repository currently contains glass effects, decorative imagery, gradients,
glows, and multiple animation styles. Migrate only the surface in scope and its
necessary shared primitives. Do not turn a feature request into a full-site
rewrite.

## Foundation

Use semantic roles rather than scattering arbitrary color values:

| Role | Tailwind starting point | Purpose |
| --- | --- | --- |
| Page | `bg-slate-50` | Quiet application background |
| Surface | `bg-white` | Cards, panels, dialogs |
| Main text | `text-slate-950` | Headings and primary content |
| Muted text | `text-slate-600` | Metadata and supporting copy |
| Border | `border-slate-200` | Separation without heavy shadow |
| Accent | `orange-700` | Primary action and selected state |
| Focus | `ring-orange-600` | Keyboard focus indication |
| Danger | `red-700` | Destructive action and error |
| Success | `emerald-700` | Completed state with text or icon |

If established CSS variables express these roles, use the variables. Keep one
accent per surface and verify contrast before shipping.

## Type and spacing

- Use one sans-serif family already loaded by the application.
- Default body text to 16px with comfortable line height.
- Use a restrained heading scale; avoid display-sized headings inside app pages.
- Constrain prose to roughly 65-75 characters per line.
- Base spacing on a 4px rhythm. Prefer common gaps of 8, 12, 16, 24, 32, and
  48px.
- Use whitespace before dividers. Add a border only when spacing cannot make the
  grouping clear.

## Surfaces and controls

- Page shell: centered container, predictable horizontal padding, no ornamental
  overlay competing with content.
- Card: opaque surface, 1px border, moderate radius, little or no shadow.
- Primary button: solid accent, concise verb label, clear hover/focus/disabled
  states.
- Secondary button: neutral outline or quiet text treatment.
- Input: persistent label, neutral border, visible focus ring, helper or error
  text below. Placeholder text is not a label.
- Navigation: emphasize the current location once. Avoid redundant active color,
  underline, glow, and scale effects together.
- Icon: normally 18-20px and paired with text when meaning is not universal.
- Dialog: focused title, short consequence, explicit cancel, and one primary or
  destructive action.

## State presentation

Use progressive disclosure for long-running document work:

1. Show a short status and the last meaningful completed stage.
2. Keep technical details collapsed unless they help the teacher recover.
3. Explain whether leaving the page is safe.
4. On failure, provide a human-readable reason and a valid next action.

Do not simulate progress percentages without backend evidence. Prefer an
indeterminate indicator and named stage.

For lesson pages, keep this priority:

1. Lesson title and learning content.
2. Progress or document readiness that affects use.
3. AI Tutor question and grounded answer area.
4. Optional generated video or other enrichment.

## Responsive behavior

- Begin with a single-column mobile reading flow.
- Introduce a sidebar only when the viewport and information hierarchy justify
  persistent parallel content.
- Keep touch targets at least 44px in either dimension where practical.
- Avoid fixed heights for translated text, errors, lesson prose, and status lists.
- Test long Vietnamese labels, filenames, and course titles for wrapping.

## Motion

- Use 100-200ms transitions for hover, focus, expand, or state change.
- Animate opacity or transform when motion is necessary; avoid layout-janking
  property animation.
- Disable nonessential motion under `prefers-reduced-motion`.
- Avoid looping gradients, waves, floating cards, pulsing glows, and typing
  effects on core learning screens.

## Simplification map

When simplifying an existing surface:

| Existing treatment | Prefer |
| --- | --- |
| Image plus gradient page background | Neutral page background |
| Translucent glass panel | Opaque bordered surface |
| Multi-color gradient button | Solid accent button |
| Glow plus large shadow | Border or subtle shadow |
| Emoji used as UI icon | Lucide icon with accessible label |
| Multiple looping animations | Static layout or one state transition |
| Generic "AI is processing" | Actual backend stage and recovery action |

Preserve recognizable brand copy and product behavior. Minimalism is reduction
of distraction, not removal of essential context, feedback, or accessibility.
