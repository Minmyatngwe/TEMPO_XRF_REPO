from __future__ import annotations

import pandas as pd
import streamlit as st


def page_header(title: str, caption: str):
    st.title(title)
    st.caption(caption)


def section_title(title: str, caption: str | None = None):
    st.subheader(title)
    if caption:
        st.caption(caption)


def records_editor(label: str, rows: list[dict], *, key: str, column_config=None):
    column_config = column_config or {}
    configured_columns = list(column_config.keys())

    if rows:
        frame = pd.DataFrame(rows)
        # Ensure optional columns are still visible even if old rows do not contain them.
        for column in configured_columns:
            if column not in frame.columns:
                frame[column] = None
        if configured_columns:
            frame = frame[configured_columns]
    else:
        # An empty DataFrame with no columns gives Streamlit nothing to add/edit.
        frame = pd.DataFrame(columns=configured_columns)

    edited = st.data_editor(
        frame,
        key=key,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config=column_config,
    )
    edited = edited.where(pd.notnull(edited), None)
    return edited.to_dict(orient="records")


def clean_records(rows: list[dict], required_field: str) -> list[dict]:
    cleaned = []
    for row in rows:
        value = row.get(required_field)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        cleaned.append(row)
    return cleaned
