# resume-send-format-contract

## binding

A resume draft written for Kevin copies the structure of his own send versions exactly and states every fact he supplied as a fact. The send versions are the canonical extracts under `shared/lappe-profile/extracts/` in the jobs-v2000 repository; a new draft descends from one of them and differs only in wording chosen for the target role.

## the-structure

Name line, headline line, contact line, a third-person summary paragraph, `SELECTED IMPACT` as a bullet list, `EXPERIENCE` entries written `Title | Company | dates` each with one paragraph and bullets in reverse chronology, an `Earlier experience:` line, an uppercase skills block with `Category: items.` bullets, and `EDUCATION`. Section labels are plain uppercase lines, never markdown headings. Bullets use `-`. `$` and `%` stay as symbols. Hyphenated compounds stay hyphenated (in-IDE, blue-green, multi-language, feature-flag). Numeric ranges use "to".

## what-never-appears-in-the-body

No first-person summary. No tailoring note, leadership essay, positioning preamble or closing commentary. No per-claim checklist. No inline marker of any kind, including `[needs-confirmation: ...]` and `[needs-research: ...]`. No hedge ("roughly" is Kevin's own wording and stays; "unverified", "reportedly" and "pending confirmation" do not). No renamed or merged sections, no roles collapsed into paragraphs, no broken chronology.

## where-the-commentary-goes

A statement in a document Kevin supplied is a fact. An open question about a figure goes in the role's `intake.md`. A note on a drafting choice (which of two supplied figures was used, what was omitted, why) goes in the role's `resume.md` under a `draft-notes` section. Neither reaches the draft body or any exported file.

## relationship-to-other-rules

This rule narrows `output-format-contract` for one artifact type and overrides two conventions that otherwise apply: the company-researcher skill's instruction to write units as words ("12 percent", "716.9 billion dollars") applies to company and role research documents, not to resume drafts; and `no-em-dash` already permits hyphenated compounds, so no compound is unhyphenated to satisfy it. `no-hardwrapped-writing` and the ban on punctuation dashes still apply inside the body.

## the-check

Before a draft is finished, diff its structure against the send version it descends from: section order, labels, bullet shape, symbols and chronology. Any difference not made deliberately for the target role is a defect and is fixed before the draft is reported as done.

## why

On 2026-09-17 Kevin rejected an Apple draft and an Amazon draft. The marker convention then in `templates/role/resume.md` in the jobs-v2000 repository and the instruction that a resume does not confirm its own claims had been applied inside the send text; the unit-in-words convention had replaced `$` and `%`; a section was renamed, the summary switched to first person, compounds lost their hyphens, three roles were collapsed into paragraphs and the chronology broke, because agents copied earlier drafts and the result was merged without a diff against the send versions. Kevin's instruction: byte for byte his structure, facts as facts, commentary only in `resume.md`.
