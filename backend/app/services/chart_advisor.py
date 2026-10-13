"""
QueryForge - Chart Type Advisor
Automatically selects the best Plotly chart type based on query result shape.
"""
from app.models.schemas import ChartConfig, ChartType, QueryColumn


def advise_chart(columns: list[QueryColumn], rows: list[list]) -> ChartConfig | None:
    """
    Given column metadata and row data, return the best chart config.
    Returns None if no chart is appropriate (e.g., single column text result).
    """
    if not columns or not rows:
        return None

    num_cols = len(columns)
    num_rows = len(rows)

    col_types = [c.type for c in columns]
    col_names = [c.name for c in columns]

    # ── 2-column results ───────────────────────────────────────────────────
    if num_cols == 2:
        t0, t1 = col_types[0], col_types[1]
        n0, n1 = col_names[0], col_names[1]

        # category + number → bar chart
        if t0 in ("text",) and t1 == "number":
            if num_rows <= 7:
                # Few categories → pie chart
                return ChartConfig(
                    type=ChartType.PIE,
                    x_column=n0,
                    y_column=n1,
                    title=f"{n1} by {n0}",
                )
            return ChartConfig(
                type=ChartType.BAR,
                x_column=n0,
                y_column=n1,
                title=f"{n1} by {n0}",
            )

        # date + number → line chart
        if t0 == "date" and t1 == "number":
            return ChartConfig(
                type=ChartType.LINE,
                x_column=n0,
                y_column=n1,
                title=f"{n1} over {n0}",
            )

        # number + number → scatter
        if t0 == "number" and t1 == "number":
            return ChartConfig(
                type=ChartType.SCATTER,
                x_column=n0,
                y_column=n1,
                title=f"{n0} vs {n1}",
            )

    # ── 1-column number result ─────────────────────────────────────────────
    if num_cols == 1 and col_types[0] == "number" and num_rows == 1:
        # Single aggregate value — show as big number card (table type)
        return ChartConfig(
            type=ChartType.TABLE,
            title=col_names[0],
        )

    # ── 3+ columns with one text + multiple numbers → grouped bar ─────────
    if num_cols >= 3:
        text_cols = [i for i, t in enumerate(col_types) if t == "text"]
        num_cols_idx = [i for i, t in enumerate(col_types) if t == "number"]
        if len(text_cols) == 1 and len(num_cols_idx) >= 1:
            return ChartConfig(
                type=ChartType.BAR,
                x_column=col_names[text_cols[0]],
                y_column=col_names[num_cols_idx[0]],
                title="Query Results",
            )

    # Default: no automatic chart (table view is shown instead)
    return None
