"""
Invoke tasks for mario.annotations project.

This module provides tasks for generating annotated event files from Mario dataset
replay files, enriching them with detailed gameplay events (actions, kills, hits, etc.).
"""

from invoke import task
import os
import os.path as op

BASE_DIR = op.dirname(op.abspath(__file__))


@task
def generate_annotations(
    c,
    datapath="sourcedata/mario",
    replays_path=None,
    clips_path=None,
    output_path="outputdata/annotated_events",
    subjects=None,
    sessions=None,
):
    """
    Generate annotated event files from Mario replay data.

    This task processes events.tsv files and enriches them with detailed gameplay events:
    - Button presses (UP, DOWN, LEFT, RIGHT, A, B, START, SELECT)
    - Enemy kills (stomp, impact, kick)
    - Hits taken (powerup lost, life lost)
    - Bricks smashed
    - Coins collected
    - Powerups collected
    - Scene traversals (if clips_path is provided)

    Parameters
    ----------
    c : invoke.Context
        The Invoke context (automatically provided).
    datapath : str, optional
        Path to the Mario dataset root directory. Default: "sourcedata/mario"
    replays_path : str, optional
        Path to mario.replays output containing game variables JSON files.
        Required to generate annotations.
    clips_path : str, optional
        Path to mario.scenes output containing scene clip metadata.
        If provided, adds scene events to annotations.
    output_path : str, optional
        Path to save annotated events files. Default: "outputdata/annotated_events"
    subjects : str, optional
        Space-separated subject IDs to process (e.g., "sub-01 sub-02").
        If None, processes all subjects.
    sessions : str, optional
        Space-separated session IDs to process (e.g., "ses-001 ses-002").
        If None, processes all sessions.

    Examples
    --------
    Generate annotations for all subjects:
    ```bash
    invoke generate-annotations --replays-path outputdata/replays
    ```

    Include scene events:
    ```bash
    invoke generate-annotations \
      --replays-path outputdata/replays \
      --clips-path outputdata/scene_clips
    ```

    Process specific subjects and sessions:
    ```bash
    invoke generate-annotations \
      --replays-path outputdata/replays \
      --subjects "sub-01 sub-02" \
      --sessions "ses-001"
    ```

    Custom paths:
    ```bash
    invoke generate-annotations \
      --datapath /data/mario \
      --replays-path /data/replays \
      --output-path /data/annotations
    ```

    Notes
    -----
    - Requires mario.replays to be processed first (--save-variables)
    - Output follows BIDS structure: sub-{sub}/ses-{ses}/func/*_desc-annotated_events.tsv
    - Scene events require mario.scenes clips to be generated first
    """
    if replays_path is None:
        print("❌ Error: --replays-path is required")
        print("   First run mario.replays with --save-variables:")
        print("   cd ../mario.replays && invoke create-replays --save-variables")
        return

    cmd = [
        "python",
        f"{BASE_DIR}/annotations/generate_annotations.py",
        "--datapath", datapath,
        "--replays_path", replays_path,
        "--output_path", output_path,
    ]

    if clips_path:
        cmd.extend(["--clips_path", clips_path])

    if subjects:
        cmd.extend(["--subjects", subjects])

    if sessions:
        cmd.extend(["--sessions", sessions])

    # Display execution info
    print("📝 Generating annotated event files...")
    print(f"   Dataset: {datapath}")
    print(f"   Replays: {replays_path}")
    if clips_path:
        print(f"   Clips: {clips_path}")
    print(f"   Output: {output_path}")
    if subjects:
        print(f"   Subjects: {subjects}")
    if sessions:
        print(f"   Sessions: {sessions}")
    print()

    # Run the annotation script
    c.run(" ".join(cmd), pty=True)

    print("✅ Annotation generation complete!")


@task
def setup_env(c):
    """
    Set up the Python environment for mario.annotations.

    Examples
    --------
    ```bash
    invoke setup-env
    ```
    """
    print("🐍 Setting up mario.annotations environment...")

    env_setup_lines = [
        "set -e",
        "python -m venv env",
        "source env/bin/activate",
        "pip install -r requirements.txt",
        "pip install -e .",
        "deactivate",
    ]

    c.run("\n".join(env_setup_lines), pty=True)
    print("✅ Environment setup complete!")
