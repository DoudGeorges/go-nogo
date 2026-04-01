# Go/No-Go Experiment

PsychoPy Go/No-Go task built for a neuroscience class, measuring the effect of background music on impulsivity and concentration.

Three auditory conditions (silence, lyrics, no lyrics) are presented in random order. Behavioral data (RT, accuracy) and EEG (Muse headband) are recorded for each trial.

## Requirements

- Python 3.10+
- [PsychoPy](https://www.psychopy.org/)
- [Pygame](https://www.pygame.org/) (audio playback)

## Usage

```bash
python go_nogo.py
```

## Input

`conditions.csv` defines the experimental blocks (one row per condition).

## Output

Each session generates a single CSV file in `data/`, named by session timestamp (e.g. `20260325_2149.csv`).

Each row is one trial and contains the condition, reaction time, accuracy, and EEG sync timestamps. Participant demographics, questionnaire responses, and block order are included in the first row.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
