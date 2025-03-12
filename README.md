# Ask ECFR

## Summary
This tool fetches information from the [Code of Federal Regulations](https://www.ecfr.gov) using its [Rest API](https://www.ecfr.gov/developers/documentation/api/v1).

## Setup
Install [uv python manager](https://docs.astral.sh/uv/getting-started/installation) for your operating system.

## Run
If you want to fetch additional LLM information for each regulation, define `OPENAI_API_KEY` in your environment.

Run with `uv`, which will fetch the required python version and all dependencies defined at the top of the file.
```
uv run main.py
```

If you see a lot of 429 throttling errors, adjust `MAX_THREADS` and `MAX_REGULATIONS_T0_FETCH` at the top of the file.

## Information
These metrics are computed using [ChatGPT o3-mini](https://openai.com/index/openai-o3-mini/) (not using o4 due to cost):

`complexity`: True if a regulation is complex. If an average adult could not understand the language, its considered complex.

`spending`: True if a regulation involves spending. This could be anything related to budget, headcount, or setting aside funds.

## Followups

- Build a full-featured data pipeline to process each regulation content (and update when it changes). Ensures the content is only downloaded and parsed once. Compute all metrics and save into a database to fetch quickly later.
- To avoid rate limit errors, implement a backoff strategy or get a privleged api key.
- Add a service on top of the database so can be accessed easily from any API or application.
- Use a chunker and embedding library to allow doing RAG queries on the content for more ad-hoc analysis.
- Some agencies have 10000+ regulations, how to fetch them without paging?
- ???
