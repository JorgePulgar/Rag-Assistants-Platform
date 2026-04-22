# FRONTEND SPEC — Visual and Interaction Design

This document is the **visual contract** for the UI. Anything concrete
about look, feel, layout, or microcopy lives here. `ARCHITECTURE.md`
defines *which* components exist; this document defines *how* they look
and behave.

If Claude Code is asked to make a visual decision that is not specified
here, it must **ask** rather than improvise.

---

## Design principles

1. **Minimal, not empty**. Generous whitespace, but every pixel has a
   reason. No decorative elements.
2. **Content first**. The UI fades; the assistant's answers and the user's
   documents are the stars.
3. **Calm professionalism**. This is a tool, not a toy. No gradients, no
   glows, no animations beyond what signals state change.
4. **Accessible by default**. Keyboard navigable, sufficient contrast,
   focus rings visible.

**Visual inspiration**: Linear, Vercel dashboard, Resend. Clean and
technical without feeling cold.

---

## Theme

**Both light and dark** with a manual toggle in the header. Default is
**system preference** (`prefers-color-scheme` media query), with a manual
override stored in `localStorage`.

Implementation: Tailwind `darkMode: 'class'`. A `<ThemeProvider>` at the
root toggles the `dark` class on `<html>`.

---

## Color palette

Use Tailwind's palette. Stick to these exact tokens unless a strong
reason exists.

### Accent (blue)

- Primary: `blue-600` (light) / `blue-500` (dark)
- Hover: `blue-700` (light) / `blue-400` (dark)
- Subtle background (selected rows, user message bubble): `blue-50`
  (light) / `blue-950/40` (dark)

### Neutrals

| Role              | Light            | Dark             |
|-------------------|------------------|------------------|
| Page background   | `white`          | `neutral-950`    |
| Card/sidebar bg   | `neutral-50`     | `neutral-900`    |
| Border            | `neutral-200`    | `neutral-800`    |
| Text primary      | `neutral-900`    | `neutral-100`    |
| Text secondary    | `neutral-600`    | `neutral-400`    |
| Text muted        | `neutral-500`    | `neutral-500`    |

### Semantic

- Success: `emerald-600` / `emerald-500`
- Error / destructive: `red-600` / `red-500`
- Warning: `amber-600` / `amber-500`

Never use raw hex. Always Tailwind tokens so the theme toggle works
transparently.

---

## Typography

**Font**: [Inter](https://fonts.google.com/specimen/Inter), loaded from
Google Fonts with `display=swap`. Fallback stack:
`Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`.

**Monospace** (for code, chunk snippets in citations):
`ui-monospace, 'SF Mono', Menlo, Monaco, Consolas, monospace`.

**Scale** (use Tailwind classes):

| Usage                 | Class          | Size    | Weight |
|-----------------------|----------------|---------|--------|
| Page title (H1)       | `text-2xl`     | 24px    | 600    |
| Section title (H2)    | `text-lg`      | 18px    | 600    |
| Card title            | `text-base`    | 16px    | 500    |
| Body                  | `text-sm`      | 14px    | 400    |
| Secondary / labels    | `text-xs`      | 12px    | 500    |
| Code / snippets       | `text-xs font-mono` | 12px | 400 |

Line height: Tailwind defaults (`leading-normal` for body,
`leading-tight` for titles).

---

## Layout

### Global layout

Fixed two-column layout on desktop:

```
┌─────────────────────────────────────────────────────────┐
│  Header (48px height)                                   │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│   Sidebar    │         Main area                        │
│   (280px     │         (flex-1)                         │
│   fixed)     │                                          │
│              │                                          │
│              │                                          │
└──────────────┴──────────────────────────────────────────┘
```

- **Header**: app name on the left (`RAG Assistants`, `text-sm font-semibold`),
  theme toggle on the right. No other content. Border-bottom.
- **Sidebar**: fixed 280px width, full height. Contains the assistant list
  and a "New assistant" button at the top. Overflow-y scroll.
- **Main area**: everything else. Route-dependent content.
- **Max width of content inside main**: 1024px, centred with horizontal
  padding of 32px.

### Mobile behaviour

**Not a priority** for the MVP. The app works on mobile in "read-only"
mode (sidebar collapses into a hamburger), but all demos are recorded
on desktop. Do not invest time in mobile polish beyond making the
sidebar collapsible. Documented as a known limitation in the README.

### Spacing scale

Follow Tailwind's 4px scale. Common spacings:
- Between sections: `space-y-6` (24px) or `space-y-8` (32px)
- Within a card: `p-4` (16px) or `p-6` (24px)
- Between form fields: `space-y-3` (12px)
- Between inline elements: `gap-2` (8px) or `gap-3` (12px)

---

## View: Assistants (sidebar content + main empty state)

**Sidebar content**:

- Header row: "Assistants" (`text-xs uppercase tracking-wide text-neutral-500`)
  + small "+ New" button (ghost variant) on the right.
- List of assistants. Each item is a row with:
  - Assistant name (`text-sm font-medium`)
  - Small secondary line with document count (`text-xs text-neutral-500`),
    e.g. "3 documents"
  - Selected state: `bg-blue-50` in light mode, `bg-blue-950/40` in dark,
    left border `border-l-2 border-blue-600`.
  - Hover state: `bg-neutral-100` / `bg-neutral-800`.
- Empty state: centred icon (MessageSquare from lucide) + "No assistants
  yet" + "Create your first assistant" button.

**Main area when no assistant is selected**:

Centred content:
- Icon (MessageSquare, 48px, `text-neutral-300` / `text-neutral-700`).
- Title: "Select an assistant to start" (`text-lg text-neutral-600`).
- Subtitle: "Or create a new one from the sidebar."
  (`text-sm text-neutral-500`).

---

## View: Assistant Detail

Shown in the main area when an assistant is selected from the sidebar
and the user is not in chat mode.

**Structure**:

1. **Header block**:
   - Assistant name as H1.
   - Description below as `text-sm text-neutral-600`.
   - Right side: two buttons — "Edit" (secondary) and "Delete"
     (destructive, ghost variant, needs confirmation dialog).

2. **Instructions section**:
   - H2 "Instructions".
   - Read-only card showing the system prompt as preformatted text.
     `bg-neutral-50` / `bg-neutral-900`, `rounded-lg`, `p-4`,
     `font-mono text-xs`, `whitespace-pre-wrap`.

3. **Documents section**:
   - H2 "Documents" with document count pill next to it.
   - Upload area: dashed-border dropzone (`border-2 border-dashed
     border-neutral-300 dark:border-neutral-700`, `rounded-lg`, `p-8`,
     centred text "Drop files here or click to upload" + file icon).
     Supports drag-and-drop and click-to-select.
   - Document list below: one row per document with:
     - File icon (lucide `FileText` for PDFs, `FileType` for DOCX, etc.)
     - Filename
     - Upload date (`text-xs text-neutral-500`)
     - Status badge: `Indexed` (emerald), `Pending` (amber with spinner),
       `Failed` (red)
     - Delete button (trash icon, ghost, destructive on hover)

4. **Conversations section** (bottom):
   - H2 "Conversations" + "Start new conversation" button on the right.
   - List of previous conversations: title + last activity timestamp.
     Click opens the chat view on that conversation.

---

## View: Chat

Shown in the main area when the user is in an active conversation.

**Structure**:

```
┌─────────────────────────────────────────┐
│  Conversation title (editable)    •••   │  ← header strip
├─────────────────────────────────────────┤
│                                         │
│                                         │
│     [message bubbles, scrollable]       │  ← main scroll area
│                                         │
│                                         │
├─────────────────────────────────────────┤
│  [textarea]                      [Send] │  ← composer (sticky bottom)
└─────────────────────────────────────────┘
```

### Message bubbles

**User message**: right-aligned, `bg-blue-600 text-white`, `rounded-2xl
rounded-br-md` (asymmetric corner), `px-4 py-2`, `max-w-[70%]`.

**Assistant message**: left-aligned, no background (plain text on page
bg), `text-neutral-900 dark:text-neutral-100`, `max-w-[85%]`.

- Avatar on assistant messages: small circle, 28px, with the assistant's
  first initial in blue.
- Whitespace between consecutive messages from the same role: `mt-1`.
  Between messages from different roles: `mt-6`.

### Citation rendering

Inline citations appear as `[1]`, `[2]`, ... right after the sentence
they support.

Each citation is a clickable pill:
- Base style: `inline-flex items-center px-1.5 py-0.5 rounded text-xs
  font-medium bg-blue-50 dark:bg-blue-950/40 text-blue-700
  dark:text-blue-300 cursor-pointer`.
- Hover: `bg-blue-100 dark:bg-blue-900/40`.
- Gap before the pill: `ml-0.5`.

Click opens a popover (shadcn `Popover`) showing:
- Document name (bold).
- Page number if available ("Page 3").
- Snippet of 300 characters in monospace with a subtle background.
- "View full document" is **not** implemented in the MVP (documented
  as future improvement).

### "Thinking" state

When the user sends a message and awaits the response:
- A placeholder bubble appears with an animated pulsing dot trio
  (`•••`) and the text "Thinking…" in `text-neutral-500`.
- Once the response arrives, the placeholder is replaced with the real
  message. No jarring transition — just content swap.

### "I don't know" state

The hardcoded "I don't have information" response renders as a normal
assistant message, but with an `AlertCircle` icon (lucide, amber) on
the left, and `text-neutral-600` instead of full primary text.
`citations` is empty, so no pills.

### Composer

- `Textarea` (shadcn), auto-growing up to 6 rows.
- Placeholder: "Ask anything about the documents…"
- `Enter` to send, `Shift+Enter` for newline.
- Send button: primary blue, disabled when empty or while thinking,
  icon-only with the `Send` lucide icon.
- Sticky at the bottom with a `border-t` above it, `p-4`.

---

## Forms and dialogs

Use shadcn's `Dialog` for: creating/editing assistants, confirming
destructive actions.

Dialog structure:
- Title: H2 style.
- Description: small secondary text below the title.
- Body: form fields with labels.
- Footer: Cancel (ghost) + primary action, right-aligned.

Form fields:
- Label above input, `text-xs font-medium text-neutral-700`.
- Input: shadcn `Input` / `Textarea`.
- Error message below input: `text-xs text-red-600 mt-1`.

---

## Microcopy

Keep it short, direct, English. Sentence case, not Title Case.

| Context                              | Text                                    |
|--------------------------------------|-----------------------------------------|
| Empty assistant list                 | "No assistants yet"                     |
| Empty document list                  | "No documents uploaded"                 |
| Empty conversation list              | "No conversations yet"                  |
| New assistant button                 | "New assistant"                         |
| Upload area                          | "Drop files here or click to upload"   |
| Send button aria-label               | "Send message"                          |
| "I don't know" default (hardcoded)   | See `RAG_SPEC.md`                       |
| Delete confirmation title            | "Delete assistant?"                     |
| Delete confirmation body             | "This will delete X documents and Y conversations. This cannot be undone." |

---

## Icons

Use [lucide-react](https://lucide.dev/). Size 16px inline, 20px for
primary UI, 48px for empty states.

Commonly needed icons:
- `MessageSquare` — chat / conversations
- `FileText`, `FileType`, `FileSpreadsheet` — documents
- `Upload` — upload button
- `Trash2` — delete
- `Pencil` — edit
- `Plus` — new / create
- `Send` — send message
- `Sun`, `Moon` — theme toggle
- `AlertCircle` — "I don't know" state
- `Loader2` — spinners (with `animate-spin`)

---

## Animations

Keep them invisible. Only animate:
- `transition-colors` on hover/focus states (duration 150ms).
- Loading spinners (`animate-spin`).
- Typing dots in "thinking" state (`animate-pulse` on each dot,
  staggered).
- Popovers / dialogs: shadcn defaults (subtle fade + scale).

**No** page transitions. **No** scroll animations. **No** entrance
animations on page load.

---

## Accessibility baseline

- All interactive elements keyboard-reachable (shadcn handles this).
- Focus rings visible: do not override shadcn's defaults.
- Color contrast ratio ≥ 4.5:1 for body text (the palette above
  satisfies this).
- Alt text on any icon that is not purely decorative (Lucide components
  accept `aria-label`).
- Dialog `esc` to close (shadcn default).

---

## What is NOT specified here

If Claude Code runs into a visual decision not covered in this
document, it must **ask Jorge** before implementing. Do not improvise
entire visual patterns. Examples of what is legitimate to ask about:

- Any new view not listed above.
- Layout alternatives for mobile beyond sidebar collapse.
- Custom chart or data viz (out of scope for this MVP).
- Animations that go beyond the ones listed.
