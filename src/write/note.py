"""Write: write today's lift note."""


def write_note(
    today_note_path,
    note_rows,
    sleep_hours,
    skipped_exercises,
    go_easy,
):
    """Write today's note. Nothing from past notes is carried over."""
    if sleep_hours is None:
        sleep_line = "Sleep not logged: sleep rules skipped."
    else:
        effort_text = "RIR 1" if go_easy else "full effort"
        sleep_line = (
            f"Sleep {sleep_hours:g}h: dropped {len(skipped_exercises)}, {effort_text}."
        )
    note_lines = [
        "---",
        "start:",
        "end:",
        f"sleep: {'' if sleep_hours is None else f'{sleep_hours:g}'}",
        "---",
        "",
        "# Fullbody",
        "",
        *note_rows,
        "",
        "## Notes",
        sleep_line,
    ]
    today_note_path.parent.mkdir(parents=True, exist_ok=True)
    today_note_path.write_text("\n".join(note_lines) + "\n")
