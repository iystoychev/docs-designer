# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack
Static HTML/CSS rendered to A4 PDF by headless Google Chrome; Python 3 standard library scripts. No framework, no build step, no third-party Python packages.

## Users
The author (a developer working with Claude Code) and the people they share results with: teammates, managers and stakeholders. Readers open the PDF after the fact, often without having seen the chat, and need the outcome, the decisions and the next steps without the conversational noise.

## Product Purpose
`docs-designer` is a Claude skill that turns a conversation, a past Claude Code session or a source file into a PDF document of one of five kinds: report, memo, guide, proposal or technical requirements. Every kind uses one shared design language, so the documents read as one family. Success: a reader understands the document's subject without any context from the conversation, and the document looks deliberately made rather than exported.

## Positioning
Claude does the editorial selection; a fixed template, stylesheet and renderer own the look. Content and kind vary; the design language never drifts.

## Operating Context
Invoked from Claude Code at the end of (or after) a working session. Output is a PDF on disk, shared by file, chat or email, read on screen and occasionally printed on A4.

## Capabilities and Constraints
- Every document shows the author's name (git `user.name` by default, overridable) and the creation date (generated at render time).
- Five kinds (report, memo, guide, proposal, requirements), each with its own front-page layout, selected by one field.
- English and Bulgarian: labels, dates and fonts support both (Latin and Cyrillic).
- Documents never mention Claude, the AI or the session that produced them.
- Body content is limited to a fixed vocabulary of semantic elements and components so the design stays consistent.
- Must render offline: fonts are vendored.

## Brand Commitments
Personal byline only. No company branding, logo or brand colors.

## Evidence on Hand
Content comes only from the session chat. Documents must never invent facts, quotes or results that are not in the chat.

## Product Principles
1. Outcome first: decisions and results lead, process follows.
2. One design language across every kind; no per-document styling.
3. Faithful to the source: nothing is fabricated.
4. Attribution is mandatory: author and date on every document.
