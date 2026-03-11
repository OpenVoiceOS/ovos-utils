
# FAQ — `ovos-utils`

## What is `ovos-utils`?
`ovos-utils` is collection of simple utilities for use across the openvoiceos ecosystem.

## How do I install it?
```bash
pip install ovos-utils
```
Or for development:
```bash
uv pip install -e ovos-utils/
```

## Where do I report bugs?
Open an issue on the GitHub repository. Ensure you are targeting the `dev` branch for fixes.

## How do I run tests?
```bash
uv run pytest ovos-utils/test/ --cov=ovos_utils
```

## How do I contribute?
1. Fork the repository and create a feature branch from `dev`.
2. Write tests for your changes.
3. Open a PR targeting the `dev` branch.
4. Ensure CI passes before requesting review.

## What Python versions are supported?
See `QUICK_FACTS.md` — currently `>=3.9`.
