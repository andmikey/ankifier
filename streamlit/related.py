import streamlit as st

st.write("# Related vocabulary")


@st.cache_data
def convert_df(df):
    return df.to_csv().encode("utf-8")


if "additional_outputs" in st.session_state:
    # TODO this can probably be displayed in a prettier way
    additional = st.session_state["additional_outputs"]

    edited_df = st.data_editor(
        additional, hide_index=True, num_rows="dynamic", use_container_width="True"
    )
