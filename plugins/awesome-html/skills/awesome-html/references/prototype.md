# Prototypes and wireframes

Clickable pages that show how a product would look and behave, in one file a partner can open.

## Decide the fidelity

- **Wireframe** when structure, navigation, or the flow is still open. Grayscale tokens, system font, real labels, gray blocks that name their content ("Chart: weekly volume"). It should look unfinished on purpose so reviewers comment on structure, not color.
- **High fidelity** when the look matters. Apply `references/design.md`. Real copy in the product's vocabulary. The effort level follows the product: an internal tool is utilitarian with care; a customer-facing or pitch screen is editorial.

## Before building

- If the screens and the main flow are not given, write the list (screen, what the user does there, where each action goes) and confirm it with the user. This is the cheapest place to catch a wrong flow.
- If the visual direction is open on a high-fidelity prototype, offer two or three small direction previews (each a token block applied to one sample screen, side by side on one page) instead of asking which style the user likes.
- If nobody can be asked (an unattended or delegated run), choose the flow or direction yourself and state the choice and the reason in your report.

## Start from `assets/prototype.html`

It has the pieces below already wired; replace the sample screens and tokens.

- **Screens.** Each screen is a `<section data-screen id="...">`. Only one is visible.
- **Every state has a URL.** The fragment is `#screen` or `#screen?key=value`: `#orders`, `#orders?state=empty`, `#order?id=1042`, `#orders?q=invoice`. The router passes the parameters to the screen's render function. This is what lets `scripts/check.py --fragment "orders?state=empty"` render a state, and lets a partner open a link straight to it.
- **State.** Everything the prototype remembers lives in one `state` object; screens render from it and from their parameters.
- **Navigation** uses plain links (`<a href="#order?id=1042">`). Actions are buttons with `data-action`; they change state, then show a toast or set `location.hash`.
- **Focus.** Moving to another screen focuses its first heading. Do not add `outline: none` for it: the template's `:focus-visible` style already hides the ring after a mouse click and shows it for keyboard users.
- **Reviewer strip.** The "Prototype" bar at the top is in normal flow, labels the data as sample data, and links every screen and state worth reviewing. Never make it a fixed overlay: fixed panels cover content in real use and in screenshots.
- **Title.** Keep one fixed `<title>`.

Mobile products: center the app in a 390 × 844 frame on wide screens and drop the frame below 600px.

## Behavior

- The main flow works end to end: navigation, the primary action, validation messages, success and failure.
- No dead controls. A control outside the prototype's scope is disabled and says so ("Not in this prototype").
- Forms: real `<label>`s, the right `type`, `inputmode`, and `autocomplete`; never block paste; errors inline next to the field.
- Buttons for actions, links for navigation; everything reachable by keyboard.
- Sample data uses the product's vocabulary and plausible values. Label it once in the reviewer strip, and again next to any figure that could be mistaken for real (a total, a revenue number, a person's name).
- No real side effects: "Open", "Download", and "Send" show a toast describing what the real product would do.
- `localStorage` is optional convenience only; wrap it in try/catch and let a reload reset the prototype.

## Check

```bash
python3 <skill-dir>/scripts/check.py page.html --fragment "orders?state=empty" --fragment "order?id=1042" ...
```

Pass one `--fragment` per screen and per required state. While iterating, `--schemes light` halves the screenshots; run both schemes before delivery. check.py renders each state at load; transient states (a toast, an in-progress spinner) are not captured, so give them a URL state if reviewers need to see them, or say they were not checked.
