import streamlit as st

# Set the title of the page
st.title("Methodology")

st.markdown("""
## Flowcharts
Below are the flowcharts representing the process for each use case:
""")

# Display the flowchart images for both calculators

st.image('./data/WSHO application.jpg', caption="Flowchart for user case 1")
st.image('./data/VSS.jpg', caption="Flowchart for user case 2")