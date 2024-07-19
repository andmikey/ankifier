import pandas as pd

import streamlit as st

st.set_page_config(page_title="Ankifier")

pg = st.navigation(
    [
        st.Page("settings.py", title="Settings"),
        st.Page("import.py", title="Import"),
        st.Page("editor.py", title="Edit"),
        st.Page("related.py", title="Related"),
    ]
)

pg.run()
