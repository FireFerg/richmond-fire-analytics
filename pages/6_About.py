import streamlit as st


st.set_page_config(
    page_title="About",
    page_icon="ℹ️",
    layout="wide",
)

st.title("ℹ️ About Richmond Fire Analytics")

st.markdown(
    """
    Richmond Fire Analytics is an independent data visualization project
    focused on Richmond Fire incident activity created by Firefighter Fergus Hughes.

    The site is designed to make incident data easier to explore through:

    - Incident trends over time
    - Engine and truck company analytics
    - District-level analysis
    - Interactive incident mapping
    - Searchable incident records

    ### Data source

    The dashboard uses incident information exported from the Richmond fire
    reporting system based off of the "Working Fire" declaration. Data is added periodically and is not updated in real time.

    ### Important notice

    This project is independent and is not an official Richmond Fire Department
    website or live dispatch system.

    Information shown here is provided for general informational and analytical
    purposes only. It should not be used for emergency response, dispatch,
    operational decision-making, or official reporting.

    ### Privacy

    Personnel names, internal validation information, and other unnecessary
    administrative fields are not displayed publicly.

    ### Contact

    Questions, corrections, or feedback can be submitted through the project's
    GitHub repository.
    """
)