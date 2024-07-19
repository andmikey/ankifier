import yaml

import streamlit as st

st.write("# Upload settings")

with open("/home/mikey/Projects/ankifier/settings/settings.yaml") as f:
    config = yaml.safe_load(f)

st.session_state["config"] = config
st.session_state["language_config_file"] = (
    "/home/mikey/Projects/ankifier/settings/language_configs/russian.yaml"
)
st.session_state["language"] = "russian"
