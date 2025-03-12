# Ask ECFR

## Summary
This tool fetches information from https://www.ecfr.gov using the API at https://www.ecfr.gov/developers/documentation/api/v1.


## Setup
Install `uv` python manager for your operating system.
https://docs.astral.sh/uv/getting-started/installation/

## Run
If you want to fetch additional LLM information for each regulation, define `OPENAI_API_KEY` in your environment.

Run with `uv`, which will fetch the required python version and all dependencies defined at the top of the file.
```
uv run main.py
```

## Information

These metrics are fetched using ChatGPT o3-mini.

`complexity`: True if a regulation is complex. If an average adult could not understand the language, its considered complex.

`spending`: True if a regulation involves spending. This could be anything related to budget, headcount, or setting aside funds.
