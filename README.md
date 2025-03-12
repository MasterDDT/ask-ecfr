# Ask ECFR

## Summary
This tool computes metrics on agency regulations from the [Code of Federal Regulations](https://www.ecfr.gov) using its [Rest API](https://www.ecfr.gov/developers/documentation/api/v1).

<img width="795" alt="Screenshot 2025-03-12 at 11 48 47 AM" src="https://github.com/user-attachments/assets/9c249744-d05c-4316-9601-36487cf6ca7c" />

## Setup
Install [uv python manager](https://docs.astral.sh/uv/getting-started/installation) for your operating system.

## Run
If you want to use an LLM to get additional insights for each regulation, define `OPENAI_API_KEY` in your environment.

Run with `uv`, which will fetch the required python version and all dependencies defined at the top of the file.
```
uv run main.py
```

If you see a lot of 429 throttling errors, adjust `MAX_THREADS` and `MAX_REGULATIONS_T0_FETCH` at the top of the file.

## Metrics
The application computes total word count and histogram of word count for regulations in a single agency. 

Also these metrics are computed using [ChatGPT o3-mini](https://openai.com/index/openai-o3-mini/) (not using o4 due to cost) if key is specified:

`complexity`: True if a regulation is complex. If an average adult could not understand the language, its considered complex.

`spending`: True if a regulation involves spending. This could be anything related to budget, headcount, or setting aside funds.

## Followups
- Handle children agencies (currently only shows top-level)
- Support historical views (i.e how has this regulation changed over time)
- Allow browsing the raw content of regulations (although some are very large)
- Support comparing agency stats against each other (requires better query performance, see below)
- Build a full-featured data pipeline to process each regulation content (and update when it changes). More efficient because the content is only downloaded and parsed once. Compute all metrics and save into a database to fetch later. Add a service on top of the database so it can be accessed easily by multiple applications. Allow filtering by any fields and comparing within or across agencies.
- To avoid rate limit errors, implement a backoff strategy or get a privileged api key.
- Use a chunker and embedding library to allow doing RAG queries on the content for more ad-hoc analysis.
- Some agencies have 10000+ regulations, how to fetch them without paging?
- Try using something like https://github.com/Yifan-Song793/RestGPT to have it infer which requests to make and have a fully automated application
