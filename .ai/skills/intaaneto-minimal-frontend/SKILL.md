---
name: intaaneto-minimal-frontend
description: Design, build, refactor, or review Intaaneto's React, Vite, and Tailwind frontend as a calm, content-first minimal interface. Use for pages, layouts, navigation, forms, lesson and AI Tutor experiences, document upload or indexing status, responsive behavior, accessibility, and simplifying gradient-, glass-, glow-, or animation-heavy UI under frontend/src.
---

# Intaaneto Minimal Frontend

Build quiet learning interfaces that make the lesson, current system state, and
next action obvious. Preserve working behavior while reducing visual and
interaction noise.

## Read Before Editing

1. Inspect the affected page, its parent layout, shared UI components, styles,
   routes, and API service. Verify the backend response instead of inventing a
   frontend contract.
2. Read `references/design-system.md` for any visual, layout, or component work.
3. Read `.ai/skills/intaaneto-rag/SKILL.md` and its routed references when the
   page concerns lessons, documents, indexing, retrieval, or AI Tutor.
4. Read `.ai/skills/intaaneto-web-security/SKILL.md` and its routed references
   when the page concerns authentication, authorization, uploads, secrets, or
   student data.
5. Check `git diff` and preserve intentional changes already in the worktree.

## Product Priorities

- Optimize for reading, teaching, uploading source material, and asking grounded
  questions. Treat generated avatars, voice, and video as optional enhancements.
- Never block lesson readiness on an optional multimedia provider such as Groq
  or D-ID when text content is otherwise usable.
- Show only processing states implemented by the backend. Do not present planned
  extraction, indexing, retrieval, or generation features as available.
- Give one primary action to each surface. Make secondary actions visually quiet.
- Keep status language concrete: what is happening, whether the user can leave,
  and what they can do after a failure.

## Visual Direction

- Prefer a neutral page background, opaque white surfaces, dark readable text,
  restrained borders, and one brand accent.
- Use spacing, alignment, typography, and grouping for hierarchy before adding
  color, shadow, or decoration.
- Avoid decorative background images, glassmorphism, backdrop blur, glow,
  excessive gradients, oversized shadows, floating ornaments, and emoji icons.
- Use the installed Lucide icon set consistently. Do not mix icon families on
  the same surface without a concrete reason.
- Limit motion to short state feedback or spatial continuity. Respect
  `prefers-reduced-motion`; never animate merely to keep the page busy.
- Keep body text comfortable to read and constrain long learning content to a
  reasonable line length.

## Interaction Rules

- Use semantic HTML and preserve native keyboard behavior.
- Provide visible focus states, explicit form labels, useful error messages, and
  status cues that do not rely on color alone.
- Use React Router links for internal navigation instead of page-reloading
  anchors.
- Cover loading, empty, error, success, disabled, and long-content states where
  they can occur. Use a spinner only when it communicates real ongoing work.
- Keep destructive actions separated from the primary flow and require clear
  confirmation where data loss is possible.
- Treat frontend role checks as presentation only. The backend must remain the
  authorization boundary.

## Implementation Workflow

1. State the user's main task and the single primary action.
2. Remove or demote elements that do not support that task.
3. Reuse existing components and tokens when they fit. Extend the smallest
   shared primitive when repetition is proven.
4. Keep page-specific data and orchestration near the page; keep reusable visual
   primitives small and free of product policy.
5. Avoid adding a component library or state dependency for a change that the
   existing React and Tailwind stack can express cleanly.
6. Make the narrowest behavioral and visual diff that achieves the task.
7. Verify the page at mobile and desktop widths and with keyboard navigation.

## RAG and Document UX

- Separate document storage, text extraction, indexing, and optional media
  generation in the interface. Do not collapse them into a vague "AI processing"
  label.
- If the API exposes stages, render a compact ordered status list such as
  uploaded, extracting, indexing, ready, or failed. If it does not, use only the
  coarser state it actually returns.
- Let a teacher retry a failed safe operation without uploading duplicates when
  the backend supports idempotency.
- For AI Tutor answers, reserve space for supporting lesson references and make
  an ungrounded or unavailable answer visibly different from a grounded answer.
- Never expose storage keys, internal prompts, provider errors, credentials, or
  content from a lesson the user is not authorized to access.

## Verification

- Run the narrowest relevant frontend tests, then `npm run lint` and
  `npm run build` from `frontend` when the change scope permits.
- Check that API calls, route guards, and existing form behavior still work.
- Inspect the final diff for unrelated restyling, duplicate CSS, hard-coded
  secrets, and claims about backend capabilities that are not implemented.
- Report skipped checks and any backend contract still needed.
