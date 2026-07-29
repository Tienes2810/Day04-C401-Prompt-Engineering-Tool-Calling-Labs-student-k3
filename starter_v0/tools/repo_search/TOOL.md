---
name: repo_search
track: custom
kind: live_api
provider: GitHub
inputs: [query, language, sort]
outputs: [items]
side_effect: false
---
# repo_search

Searches GitHub open-source repositories for code, libraries, and frameworks.
`query` is the search keyword, `language` filters by programming language, and `sort` specifies sorting criteria (`stars`, `forks`, `updated`).
