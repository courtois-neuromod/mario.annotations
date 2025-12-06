"""
Invoke tasks for mario.annotations project using airoh.

This module provides tasks for creating annotated event files from Mario dataset
replay files, enriching them with detailed gameplay events (actions, kills, hits, etc.).
"""

from invoke import task
import os
import os.path as op

BASE_DIR = op.dirname(op.abspath(__file__))


@task
def create_annotations(
    c,
    datapath=None,
    replays_path=None,
    clips_path=None,
    output=None,
    subjects=None,
    sessions=None,
):
    """
    Create annotated event files from Mario replay data.

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
        Path to the Mario dataset root directory. Defaults to mario_dataset from invoke.yaml.
    replays_path : str, optional
        Path to mario.replays output containing game variables JSON files.
        Defaults to replays_path from invoke.yaml (required).
    clips_path : str, optional
        Path to mario.scenes output containing scene clip metadata.
        Defaults to clips_path from invoke.yaml. If provided, adds scene events to annotations.
    output : str, optional
        Path to save annotated events files. Defaults to output_dir from invoke.yaml.
    subjects : str, optional
        Space-separated subject IDs to process (e.g., "sub-01 sub-02").
        If None, processes all subjects.
    sessions : str, optional
        Space-separated session IDs to process (e.g., "ses-001 ses-002").
        If None, processes all sessions.

    Examples
    --------
    Create annotations with default settings from invoke.yaml:
    ```bash
    invoke create-annotations
    ```

    Include scene events:
    ```bash
    invoke create-annotations --clips-path outputdata/scene_clips
    ```

    Process specific subjects and sessions:
    ```bash
    invoke create-annotations --subjects "sub-01 sub-02" --sessions "ses-001"
    ```

    Custom paths:
    ```bash
    invoke create-annotations \
      --datapath /data/mario \
      --replays-path /data/replays \
      --output /data/annotations
    ```

    Notes
    -----
    - Requires mario.replays to be processed first (--save-variables)
    - Output follows BIDS structure: sub-{sub}/ses-{ses}/func/*_desc-annotated_events.tsv
    - Scene events require mario.scenes clips to be generated first
    """
    # Resolve paths from configuration or arguments
    if datapath is None:
        datapath = c.config.get("mario_dataset", "sourcedata/mario")

    if replays_path is None:
        replays_path = c.config.get("replays_path", None)

    if replays_path is None:
        print("❌ Error: --replays-path is required")
        print("   Set it in invoke.yaml or pass --replays-path")
        print("   First run mario.replays with --save-variables:")
        print("   cd ../mario.replays && invoke create-replays --save-variables")
        return

    if clips_path is None:
        clips_path = c.config.get("clips_path", None)

    if output is None:
        output = c.config.get("output_dir", "outputdata/annotated_events")

    cmd = [
        "python",
        f"{BASE_DIR}/code/mario_annotations/annotations/generate_annotations.py",
        "--datapath", datapath,
        "--replays_path", replays_path,
        "--output_path", output,
    ]

    if clips_path:
        cmd.extend(["--clips_path", clips_path])

    if subjects:
        cmd.extend(["--subjects", subjects])

    if sessions:
        cmd.extend(["--sessions", sessions])

    # Display execution info
    print("📝 Creating annotated event files...")
    print(f"   Dataset: {datapath}")
    print(f"   Replays: {replays_path}")
    if clips_path:
        print(f"   Clips: {clips_path}")
    print(f"   Output: {output}")
    if subjects:
        print(f"   Subjects: {subjects}")
    if sessions:
        print(f"   Sessions: {sessions}")
    print()

    # Run the annotation script
    c.run(" ".join(cmd), pty=True)

    print("✅ Annotation creation complete!")


@task
def setup_env(c):
    """
    Set up the Python environment for mario.annotations.

    Parameters
    ----------
    c : invoke.Context
        The Invoke context.

    Examples
    --------
    ```bash
    invoke setup-env
    ```
    """
    print("🐍 Setting up mario.annotations environment...")
    print("📦 Installing required packages...")

    env_setup_lines = [
        "set -e",
        "python -m venv env",
        "source env/bin/activate",
        "which python",
        "pip install -e .",
        "deactivate",
    ]

    c.run("\n".join(env_setup_lines), pty=True)
    print("✅ Environment setup complete!")
