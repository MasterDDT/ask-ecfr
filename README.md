# Ask ECFR

## Summary
This tool computes metrics on agency regulations from the [Code of Federal Regulations](https://www.ecfr.gov) using its [Rest API](https://www.ecfr.gov/developers/documentation/api/v1).

<img width="300" alt="Screenshot 2025-03-12 at 11 48 47 AM" src="https://github.com/user-attachments/assets/9c249744-d05c-4316-9601-36487cf6ca7c" />

## Setup
Install [uv python manager](https://docs.astral.sh/uv/getting-started/installation) for your operating system.

## Run
If you want to use an LLM to get additional insights for each regulation, define `OPENAI_API_KEY` in your environment.

Run with `uv`, which will fetch the required python version and all dependencies defined at the top of the file.
```
uv run main.py
```

If you see a lot of 429 throttling errors, decrease `MAX_THREADS` and `MAX_REGULATIONS_T0_FETCH` environment variables (default 4 and 100). Conversely if app is too slow, increase those values.

## Usage
At the top, select a single application. You will then get `total word count` and word count frequency for each regulation.

Also these pie charts are computed using [ChatGPT o3-mini](https://openai.com/index/openai-o3-mini/) (not using o4 due to cost) if key is specified:

`complexity`: True if a regulation is complex. If an average adult could not understand the language, its considered complex.

`spending`: True if a regulation involves spending. This could be anything related to budget, headcount, or setting aside funds.

## Followups
- Handle children agencies separately (currently only shows top-level)
- Support historical views (i.e how has this regulation changed over time)
- Allow browsing the raw content of regulations (although some are very large)
- More metrics and filtering (i.e by date)
- Support comparing agency stats against each other (requires better query performance, see below)
- Implement a backoff strategy for rate limits to allow more threads
- Some agencies have 10000+ regulations, how to fetch them without paging?

## Long-term
- Build a full-featured data pipeline to process each regulation content along with updates. Ensure content is only downloaded and parsed once. Compute all metrics and save into a database to fetch later. Add a service on top of the database so it can be accessed easily by multiple applications. Allow filtering by any fields and comparing within or across agencies, with time-travel for historial data.
- Use a chunker and embedding library to allow RAG question-answer interface on the content for more ad-hoc analysis (i.e show me regulations that involve X and Y)
- Try using something like https://github.com/Yifan-Song793/RestGPT to have it build this interface ad-hoc, fully automated
