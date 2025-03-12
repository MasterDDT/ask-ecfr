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
