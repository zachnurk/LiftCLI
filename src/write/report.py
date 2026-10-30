"""Write: print the arrow table for chat."""


def box_table(header_cells, body_rows):
    """Draw rows as a Unicode box-drawing table for the chat report."""
    all_rows = [header_cells, *body_rows]
    column_widths = []
    for column_index in range(len(header_cells)):
        widest_cell = max(len(str(row[column_index])) for row in all_rows)
        column_widths.append(widest_cell)

    def border_line(left_corner, middle_joint, right_corner):
        dash_runs = ["─" * (width + 2) for width in column_widths]
        return left_corner + middle_joint.join(dash_runs) + right_corner

    def cell_line(row):
        padded_cells = [
            f" {cell!s:<{width}} " for cell, width in zip(row, column_widths)
        ]
        return "│" + "│".join(padded_cells) + "│"

    table_lines = [border_line("┌", "┬", "┐"), cell_line(header_cells)]
    table_lines.append(border_line("├", "┼", "┤"))
    for body_row in body_rows:
        table_lines.append(cell_line(body_row))
    table_lines.append(border_line("└", "┴", "┘"))
    return "\n".join(table_lines)


def print_report(today_note_path, report_rows):
    """Print where the note went and the arrow table for chat."""
    print(f"Wrote {today_note_path}\n")
    print(box_table(("Exercise", "Weight", "Last", "Aim", "Rule"), report_rows))
