# OCEAN Personality Test

Streamlit application for IPIP-NEO-120 personality assessment (OCEAN/Big Five).

## Overview

The OCEAN personality test measures five personality dimensions:
- **O** - Openness to Experience
- **C** - Conscientiousness
- **E** - Extraversion
- **A** - Agreeableness
- **N** - Neuroticism

## Location

- **App:** `app/ocean-test/personality_test_app.py`
- **Data:** `app/src/data/ocean-test/`

## Running

From the project root:

```bash
streamlit run app/ocean-test/personality_test_app.py
```

Or from the app/ocean-test directory:

```bash
cd app/ocean-test
streamlit run personality_test_app.py
```

## Data Files

Located in `app/src/data/ocean-test/`:
- `questions_ipip_neo_120.json` - 120 IPIP-NEO questions
- `get-template-en.json` - Domain descriptions and interpretations
- `big_5_test.csv` - Alternative CSV format
- `ipip_neo_results.json` - Saved test results (generated)

## Features

- 120-question IPIP-NEO assessment
- Progress tracking during test
- Interactive radar chart visualization
- Facet breakdown charts for each domain
- Detailed interpretations
- Results saving to JSON
- Feedback form

## Integration

The OCEAN test button in the Dashboard (`/dashboard`) can link to this Streamlit app by running it on a separate port, or it can be integrated into the React app in the future.
