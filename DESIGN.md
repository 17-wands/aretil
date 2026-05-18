# aretil Design System

A direct, high-confidence design system for legal-technology products that turn a
law firm's experience data into fast, sourced answers — covering experience
management, business development, pitch and proposal generation, matter
intelligence, and AI-native query.

> **Disclaimer — proof of concept.** `aretil` is an unaffiliated proof of concept
> built for product exploration. It is not production software, and is not
> affiliated with, authorized by, or endorsed by Litera or any other company named
> in these documents. Its demo dataset is a synthetic assembly seeded from public
> SEC EDGAR filings — the client companies, deals, and counsel are real and
> public; the law firm, its timekeepers, and deal values are fictional. It is
> built entirely from publicly available information, with no confidential or
> insider knowledge. Competitive references reflect public
> information at a point in time and may be incomplete or out of date. Provided
> as-is, without warranty.

## 1. Brand Positioning

### Core idea
A law firm's experience, structured to answer.

aretil should communicate that the product turns scattered matter, client, and
timekeeper history into a layer that answers real business-development questions
in seconds. The brand should feel precise, fast, evidence-led, and technically
advanced without relying on legal nostalgia, prestige signaling, or generic
law-firm visual language.

### Brand promise
Make the firm's experience instantly usable.

### Audience
- Business-development and proposals teams, practice-group leaders, partners,
  knowledge-management directors, firm leadership, investors, and technical
  recruits.
- Buyers who value speed, accuracy, sourcing, fast onboarding, and trustworthy
  output.
- Users who need confidence that an answer is grounded in the firm's real matters
  and can be traced back to them.

### Personality traits
- Evidence-led
- Precise
- Decisive
- Technical
- Responsive
- Composed
- Unembellished

### What the brand should avoid
- Legal cliché (gavels, scales of justice, columns, marble, mahogany)
- Stuffy traditional law-firm prestige aesthetics
- Glossy AI-hype futurism
- Fragile startup minimalism
- Generic legal stock imagery without context
- Claims that imply capability without proof
- Decorative complexity that hurts comprehension

## 2. Voice and Messaging

### Voice principles
1. **Directness is credibility** — say what the product does and why it matters.
2. **Outcomes before features** — connect capability to business-development
   results: won work, faster proposals, sourced answers.
3. **Speed with accuracy** — communicate fast turnaround without implying the
   answer is unchecked.
4. **Data layer and AI together** — show that the structured data and the model
   are designed to work as one system.
5. **Proof in the work product** — prioritize real matters, sourced citations,
   and demonstrated speed.

### Message architecture

#### Hero formula
`The firm's experience, ready for [business-development outcome].`

Examples:
- The firm's experience, ready for the next pitch.
- Structured matter data for fast, sourced answers.
- Every relevant matter, found and cited in seconds.

#### Subhead formula
`Turn [firm data] into [outcome] with a layer built for speed, accuracy, and trust.`

Examples:
- Turn matter, client, and timekeeper data into drafted pitches with a layer built for speed, accuracy, and trust.
- Connect the firm's experience to Claude through one inspectable data layer.

#### Proof points
- Sourced answers
- Resolved entities
- Matter coverage
- Days to value
- Inspectable queries
- Local-first deployment
- MCP-native access

### Tone by surface
- **Homepage:** bold, controlled, outcome-led.
- **Capability pages:** specific, technical, outcome-driven.
- **Product pages:** performance facts, workflow context, system role.
- **Recruiting:** urgency, ownership, engineering difficulty.
- **Security and compliance pages:** credible, precise, procurement-aware.
- **UI microcopy:** terse, operational, unambiguous.

### Preferred words
Matter, client, timekeeper, practice, pitch, proposal, experience, sourced,
resolved, query, retrieve, jurisdiction, deal, evidence, structured, inspectable,
fast, accurate, coverage, data layer, firm, system.

### Words to use sparingly
Revolutionary, game-changing, AI-powered, magical, disruptive, seamless,
futuristic, next-gen.

## 3. Visual Direction

### Design philosophy
aretil uses stark contrast, technical typography, dense information hierarchy, and
product-interface imagery. It should feel engineered for use, not decoration. The
design should suggest speed, precision, and operational readiness.

### Visual attributes
- Black and near-black foundations
- Sand, bone, and steel neutrals
- Controlled red or amber accents
- High-contrast interface and data imagery
- Dense but legible data overlays
- Technical diagrams
- Modular grids
- Hard edges balanced with practical radius
- Condensed labels and specifications

### Composition
Use strong horizontal and vertical structure. Favor split layouts, evidence cards,
specification tables, large interface imagery, and result-list overlays. Avoid
whimsical layouts and soft pastel systems.

## 4. Color System

### Primary palette
- **Blackout** — `#050505` — primary background
- **Carbon** — `#111111` — elevated background
- **Graphite** — `#1B1C1D` — panels
- **Steel** — `#3C4147` — borders and secondary surfaces
- **Gunmetal** — `#687078` — secondary text
- **Bone** — `#E6E0D2` — warm foreground
- **White** — `#FFFFFF` — high-emphasis text

### Tactical neutrals
- **Sand** — `#B9A98B`
- **Khaki** — `#8F8064`
- **Olive Black** — `#1F241E`
- **Dust** — `#D0C7B8`

### Accent palette
- **Signal Red** — `#FF3B30` — critical action, alert, emphasis
- **Warning Amber** — `#FFB020` — caution, pending, active scan
- **Target Green** — `#6EE778` — confirmed, online, tracked
- **Command Blue** — `#4DA3FF` — friendly, selected, system control
- **Infra Violet** — `#8B5CF6` — AI inference, model state, autonomy layer

### Usage rules
- Black, carbon, and graphite should dominate.
- Use sand and bone to humanize dark compositions.
- Red is powerful; reserve it for decisive emphasis or critical status.
- Green indicates confirmation, not decoration.
- Amber indicates active process, scan, or caution.

## 5. Typography

### Type personality
Typography should feel engineered, compressed, and durable. Use a strong
sans-serif for brand messaging and a technical monospace for data-heavy surfaces.

### Recommended font stack
- **Primary sans:** Neue Haas Grotesk, Inter, Söhne, Helvetica Neue, Arial, sans-serif
- **Condensed display:** DIN Condensed, Roboto Condensed, Archivo Narrow, sans-serif
- **Monospace:** IBM Plex Mono, JetBrains Mono, SF Mono, Roboto Mono, monospace

### Type scale
- **Display XL:** 84/84, weight 700, tracking `-0.055em`
- **Display L:** 64/68, weight 700, tracking `-0.045em`
- **H1:** 48/54, weight 700, tracking `-0.035em`
- **H2:** 36/42, weight 700, tracking `-0.025em`
- **H3:** 24/30, weight 650
- **Body L:** 18/28, weight 400
- **Body:** 15/24, weight 400
- **Small:** 13/18, weight 500
- **Label:** 11/14, weight 700, tracking `0.08em`, uppercase
- **Data:** 12/18, monospace, weight 500

### Typography rules
- Headlines may be large and blunt.
- Labels should be uppercase and compact.
- Use monospace for IDs, matter numbers, model states, latency, and specs.
- Avoid long poetic headlines.
- Keep line lengths short on decision-critical copy.

## 6. Layout and Grid

### Grid
- Desktop max width: 1280 px
- Wide max width: 1600 px
- Columns: 12
- Gutter: 24 px
- Base spacing unit: 4 px
- Dense operational UI may use an 8 px subgrid.

### Spacing scale
- `4` precision alignment
- `8` dense technical grouping
- `12` compact controls
- `16` component padding
- `24` cards and modules
- `40` content blocks
- `64` section rhythm
- `96` major page rhythm
- `128` campaign-scale rhythm

### Layout patterns
- **Evidence split:** copy on one side, an interface or result view on the other.
- **Capability matrix:** workflows, data sources, and outcomes in a modular grid.
- **Spec stack:** an interface visual paired with performance data.
- **Result console:** a background data view with overlays and controls.
- **Query console:** dense interface showing parse, retrieve, resolve, draft, cite.

## 7. Components

### Buttons
#### Primary
- Background: Signal Red or Bone depending on context
- Text: Blackout for light buttons, White for red buttons
- Radius: 4 px
- Padding: 12 px 18 px
- Text: Label style or 14 px semibold
- Hover: increase brightness 8%

#### Secondary
- Background: transparent
- Border: 1 px solid Steel
- Text: Bone
- Hover: background `rgba(230,224,210,0.08)`

#### Tactical text link
- Text: Bone
- Underline: 1 px, offset 4 px
- Hover: Signal Red

### Cards
- Radius: 8 px
- Border: 1 px solid `rgba(230,224,210,0.14)`
- Background: `#111111`
- Header: uppercase label
- Footer: data row or status chip

### Spec modules
- Use compact rows with label, value, and unit.
- Values should be monospace or tabular numeric.
- Include source context only when available in the matter content.

Example:
- MATTERS / 84
- PRACTICE / M&A
- JURISDICTION / DELAWARE
- ROLE / LEAD COUNSEL

### Status indicators
- **Resolved:** Target Green
- **Indexing:** Warning Amber
- **Conflict:** Signal Red
- **Manual review:** Command Blue
- **Agent (MCP):** Infra Violet
- **Offline:** Gunmetal

### Inputs
- Height: 40 px
- Radius: 4 px
- Background: `#050505`
- Border: `#3C4147`
- Focus: `0 0 0 2px rgba(255,176,32,0.36)`
- Placeholder: Gunmetal

## 8. Iconography

### Style
- Angular, geometric, functional
- 1.75 px or 2 px strokes
- Minimal curves
- Built on 24 px grid
- Optional cut-corner containers

### Icon themes
- Matter record
- Search and retrieve
- Entity resolution
- MCP connection
- Sourced citation
- Practice coverage
- Local data layer
- Pitch and proposal
- Jurisdiction

### Rules
- Avoid decorative badges unless tied to real status.
- Avoid gavels, scales of justice, and generic legal clip-art.
- Icons should help the user understand function or state.

## 9. Imagery

### Interface imagery
Use high-contrast captures of the product — query results, matter cards, sourced
citations, the data console, and the visible SQL behind an answer. The product
should look precise, fast, and engineered.

### Image treatment
- Slight desaturation
- High contrast
- Deep shadows
- Warm highlights
- Optional grain at 2–4% opacity
- Technical overlays in monochrome, amber, green, or red

### Overlay patterns
- Result counts
- Source citations
- Confidence markers
- Entity links
- Query parameters
- Latency readouts
- Workflow phase labels

### Avoid
- Fake holograms
- Excessive lens flare
- Generic legal stock imagery
- Gavels, courtrooms, and prestige clichés
- Decorative UI overlays that obscure the content

## 10. Motion

### Motion principles
- Fast, mechanical, purposeful
- Motion should imply readiness and state transition
- Avoid elastic or playful easing

### Durations
- Micro interactions: 90–140 ms
- Console updates: 160–220 ms
- Page transitions: 280–420 ms
- Hero reveals: 500–650 ms

### Easing
- Use `cubic-bezier(0.2, 0, 0, 1)` for decisive UI motion.
- Use linear motion for indexing or progress loops.

### Common motion patterns
- Result reveal
- Entity-resolution confirmation
- Latency value updates
- Filter toggles
- Workflow phase step advances
- Source-citation reveal

## 11. Data Visualization

### Chart style
- Dense, high-contrast, operational
- Thin grid lines
- Minimal ornament
- Monospace labels
- Clear status colors

### Visualization types
- Matter timelines
- Result tables
- Practice coverage grids
- Deal-value distributions
- Jurisdiction maps
- Workflow sequence charts
- Experience coverage dashboards

### Rules
- Every visualization should answer a real business-development question.
- Use units consistently.
- Label confidence and uncertainty when relevant.
- Do not overload red; use it only when something is truly critical.

## 12. Web Page Patterns

### Homepage structure
1. Outcome-led hero.
2. Proof of speed and sourcing.
3. Data-layer overview.
4. Workflow modules.
5. Use-case scenarios.
6. Architecture: data layer and AI.
7. Customer credibility.
8. Demo or contact CTA.

### Capability page structure
1. The business-development problem.
2. Capability claim.
3. System diagram.
4. Workflow modules.
5. Evidence of speed and accuracy.
6. Onboarding pathway.
7. Contact CTA.

### Recruiting page structure
1. Why the problem matters.
2. Engineering difficulty.
3. Ownership model.
4. Teams and disciplines.
5. Benefits and expectations.
6. Open roles.

## 13. UI Copy Patterns

### Alert
`Potential conflict detected.`

### Confirmation
`Pitch drafted.`

### Manual review
`Reviewer approval required.`

### Autonomy disclosure
`Agent draft. Human review pending.`

### Offline state
`Data layer unavailable. Last sync: 14:32.`

### Loading state
`Querying matter data…`

### Error state
`Query failed. Verify the data layer and try again.`

## 14. Accessibility

### Requirements
- Minimum body contrast: 4.5:1
- Large display contrast: 3:1 minimum
- Never communicate status by color alone
- Use readable labels for data overlays and icons
- Support reduced motion for indexing and progress animations
- Keep critical controls large enough for comfortable primary-workflow use
- Provide keyboard-accessible controls for query interfaces

## 15. Implementation Tokens

```css
:root {
  --ds-blackout: #050505;
  --ds-carbon: #111111;
  --ds-graphite: #1B1C1D;
  --ds-steel: #3C4147;
  --ds-gunmetal: #687078;
  --ds-bone: #E6E0D2;
  --ds-white: #FFFFFF;

  --ds-sand: #B9A98B;
  --ds-khaki: #8F8064;
  --ds-olive-black: #1F241E;
  --ds-dust: #D0C7B8;

  --ds-signal-red: #FF3B30;
  --ds-warning-amber: #FFB020;
  --ds-target-green: #6EE778;
  --ds-command-blue: #4DA3FF;
  --ds-infra-violet: #8B5CF6;

  --ds-radius-sm: 4px;
  --ds-radius-md: 8px;
  --ds-radius-lg: 12px;

  --ds-focus: 0 0 0 2px rgba(255,176,32,0.36);
  --ds-shadow-hard: 0 20px 70px rgba(0,0,0,0.55);
}
```

## 16. Brand Checklist

Before shipping an aretil asset, confirm:
- The message is outcome-led and specific.
- The visual system feels engineered, not decorative.
- Claims are backed by sourced results, speed, or matter coverage.
- Interface imagery or system diagrams do real explanatory work.
- Typography is blunt, legible, and controlled.
- Red is used intentionally.
- The final asset feels precise, fast, and credible.
