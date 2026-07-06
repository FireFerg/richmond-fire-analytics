import streamlit as st


def chart_card(title, subtitle, footer_left=None, footer_right=None):
    st.markdown(
        f"""
        <div class="chart-card">
            <div class="chart-title">{title}</div>
            <div class="chart-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )

    chart_placeholder = st.container()

    if footer_left or footer_right:
        st.markdown(
            f"""
            <div class="chart-footer">
                <span>{footer_left or ""}</span>
                <span>{footer_right or ""}</span>
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("</div>", unsafe_allow_html=True)

    return chart_placeholder