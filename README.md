# mario.annotations

Generate fine-grained event annotations from Super Mario Bros replay data. Enriches basic event files with detailed gameplay events including button presses, enemy interactions, item collection, and scene traversals.

## What You Get

For each run's `events.tsv` file, generates an enriched `*_desc-annotated_events.tsv` containing:

### Action Events
- **Button presses**: UP, DOWN, LEFT, RIGHT, A, B, START, SELECT
- Each event includes onset, duration, and frame positions

### Combat Events
- **Enemy kills** with type classification:
  - Stomp kills (jumping on enemies)
  - Impact kills (shell/fireball hits)
  - Kick kills (kicked shell hits)

### Damage Events
- **Hits taken**:
  - Powerup lost (big → small Mario)
  - Life lost (death)

### Collection Events
- **Coins collected**: Timing of each coin pickup
- **Powerups collected**: Mushroom/fire flower collection
- **Bricks smashed**: Brick breaking events

### Scene Events (Optional)
- **Scene traversals**: Boundaries and timing of atomic scene segments
- Requires mario.scenes clips to be generated first

## Quick Start

```bash
# Install
cd mario.annotations
pip install -r requirements.txt
pip install -e .

# Or with airoh
invoke setup-env

# Generate annotations (requires mario.replays output)
invoke generate-annotations --replays-path ../mario.replays/outputdata/replays
```

## Usage

### With Airoh (Recommended)

```bash
# Basic annotation generation
invoke generate-annotations --replays-path outputdata/replays

# Include scene events
invoke generate-annotations \
  --replays-path outputdata/replays \
  --clips-path outputdata/scene_clips

# Process specific subjects and sessions
invoke generate-annotations \
  --replays-path outputdata/replays \
  --subjects "sub-01 sub-02" \
  --sessions "ses-001"

# Custom paths
invoke generate-annotations \
  --datapath /data/mario \
  --replays-path /data/replays \
  --output-path /data/annotations
```

### Direct Python Script

```bash
python annotations/generate_annotations.py \
  --datapath sourcedata/mario \
  --replays_path outputdata/replays \
  --output_path outputdata/annotated_events \
  --subjects sub-01 sub-02 \
  --sessions ses-001
```

## Requirements

- Python ≥ 3.8
- Mario dataset with events.tsv files
- **mario.replays output** (processed with `--save-variables`)
- stable-retro
- mario.scenes output (optional, for scene events)

## Prerequisites

Before generating annotations, you must first process replays with mario.replays:

```bash
cd ../mario.replays
invoke create-replays --save-variables --output outputdata/replays
cd ../mario.annotations
```

For scene events, also generate clips with mario.scenes:

```bash
cd ../mario.scenes
invoke create-clips --output outputdata/scene_clips
cd ../mario.annotations
```

## Output Structure

```
outputdata/annotated_events/
└── sub-XX/
    └── ses-XXX/
        └── func/
            └── sub-XX_ses-XXX_run-XX_desc-annotated_events.tsv
```

## Available Tasks

```bash
invoke --list                    # View all tasks
invoke setup-env                 # Install dependencies
invoke generate-annotations      # Generate annotated events
```

### Task Options

- `--datapath` - Mario dataset location (default: sourcedata/mario)
- `--replays-path` - Path to mario.replays output (required)
- `--clips-path` - Path to mario.scenes clips (optional, for scene events)
- `--output-path` - Output directory (default: outputdata/annotated_events)
- `--subjects` - Space-separated subject IDs (e.g., "sub-01 sub-02")
- `--sessions` - Space-separated session IDs (e.g., "ses-001 ses-002")

## Data Format

### Annotated Events TSV

Tab-separated file with columns:

```
onset       duration    trial_type              level    frame_start  frame_stop
0.000       0.000       gym-retro_game          w1l1     0            2718
0.000       1.250       RIGHT                   w1l1     0            75
1.283       0.100       A                       w1l1     77           83
2.450       0.000       Kill/stomp              w1l1     147          147
3.567       0.000       Coin_collected          w1l1     214          214
4.100       0.000       Powerup_collected       w1l1     246          246
5.233       0.000       Brick_smashed           w1l1     314          314
6.450       0.000       Hit/life_lost           w1l1     387          387
7.000       3.500       scene-w1l1s1_code-...   w1l1     420          630
```

### Event Types

| Type                    | Description                              |
| ----------------------- | ---------------------------------------- |
| `gym-retro_game`        | Full replay/repetition metadata          |
| `UP`, `DOWN`, etc.      | Button press actions                     |
| `Kill/stomp`            | Enemy killed by jumping                  |
| `Kill/impact`           | Enemy killed by shell/fireball           |
| `Kill/kick`             | Enemy killed by kicked shell             |
| `Hit/powerup_lost`      | Powerup downgrade (big → small)          |
| `Hit/life_lost`         | Death event                              |
| `Coin_collected`        | Coin pickup                              |
| `Powerup_collected`     | Mushroom/fire flower collection          |
| `Brick_smashed`         | Brick breaking                           |
| `scene-{scene}_code-*`  | Scene traversal (requires --clips-path)  |

## Processing Specific Subjects/Sessions

You can filter processing to specific subjects and sessions:

```bash
# Process only sub-01 and sub-02
invoke generate-annotations \
  --replays-path outputdata/replays \
  --subjects "sub-01 sub-02"

# Process only session 001
invoke generate-annotations \
  --replays-path outputdata/replays \
  --sessions "ses-001"

# Combine filters
invoke generate-annotations \
  --replays-path outputdata/replays \
  --subjects "sub-01" \
  --sessions "ses-001 ses-002"
```

## Troubleshooting

**"replays_path is required"**: Run mario.replays first with `--save-variables`

**"No variables sidecar found"**: Ensure mario.replays output path is correct and variables were saved

**Missing scene events**: Provide `--clips-path` pointing to mario.scenes output

## Related Projects

- [mario](https://github.com/courtois-neuromod/mario) - Main dataset
- [mario.replays](https://github.com/courtois-neuromod/mario.replays) - Replay processing (required)
- [mario.scenes](https://github.com/courtois-neuromod/mario.scenes) - Scene analysis (optional)

Part of the [Courtois NeuroMod](https://www.cneuromod.ca/) project.
