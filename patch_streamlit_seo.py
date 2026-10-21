from pathlib import Path
import streamlit as st


TITLE = "RVA Fire Data | Richmond Fire Incident Analytics"

DESCRIPTION = (
    "Explore Richmond, Virginia fire incident data and analytics, "
    "including incident trends, company activity, districts, maps, "
    "and response statistics."
)


# Locate Streamlit's installed frontend HTML automatically.
index_path = Path(st.__file__).parent / "static" / "index.html"

html = index_path.read_text(encoding="utf-8")


# Replace Streamlit's default title.
html = html.replace(
    "<title>Streamlit</title>",
    f"<title>{TITLE}</title>",
)


# Replace Streamlit's default noscript message.
html = html.replace(
    "<noscript>You need to enable JavaScript to run this app.</noscript>",
    f"<noscript>{DESCRIPTION}</noscript>",
)


# Add SEO metadata if it isn't already present.
if 'name="description"' not in html:
    seo_tags = f"""
    <meta name="description" content="{DESCRIPTION}" />

    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://rvafiredata.com/" />
    <meta property="og:title" content="{TITLE}" />
    <meta property="og:description" content="{DESCRIPTION}" />

    <meta name="twitter:card" content="summary" />
    <meta name="twitter:title" content="{TITLE}" />
    <meta name="twitter:description" content="{DESCRIPTION}" />
    """

    html = html.replace(
        "</head>",
        f"{seo_tags}\n</head>",
    )


index_path.write_text(html, encoding="utf-8")

print(f"Patched Streamlit SEO metadata: {index_path}")