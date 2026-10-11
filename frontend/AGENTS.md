<!-- LOVABLE:BEGIN -->

> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.

<!-- LOVABLE:END -->

## Architecture rules

- All backend calls go through the `AssistantApi` interface in `src/services/api.ts`; only a mock implementation exists until the FastAPI backend is ready, so swapping is a one-line change.
- Generated HTML artifacts render only inside an iframe with `sandbox=""` and `srcDoc`; never inject untrusted HTML into the app DOM.
- Conversation state lives in a React context store and is persisted to localStorage, hydrated in an effect to avoid SSR mismatches.

- Assistant presentation uses shared semantic dark tokens and shadcn Button controls; this keeps interaction states coherent without changing the mock service or store.
- Artifact previews use a split pane on wide screens and a sheet below 1100px, so chat and history remain usable without clipped content.
