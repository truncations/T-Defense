# Local demo backups

Browser tests generate screenshots here; tools/record_demo.py records a silent walkthrough. These generated PNG/WebM files stay on the builder's machine and are excluded from the public source snapshot. Original local stage commits and recordings are preserved on the local stage-history archive branch when synchronizing publication through the GitHub connection.

Use only synthetic examples. Replay recordings are UI walkthroughs, not new live investigations. The current recording filename is gate-walkthrough.webm; its exact evidence mode is displayed in the video. Tests own port8000, so stop a manual server before running them or the recorder.
