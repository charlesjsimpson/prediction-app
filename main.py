import streamlit as st

# Simple Hello World app
st.title("Hello World!")
st.header("Welcome to the Hotel Financial Dashboard")

st.write("This is a simple test to make sure Streamlit is working correctly.")

st.success("Everything is working as expected!")

# Add a button to continue to the main app
if st.button("Continue to Dashboard"):
    # In a real app, this would navigate to the main dashboard
    st.session_state.show_dashboard = True

# Check if we should show the dashboard
if st.session_state.get('show_dashboard', False):
    st.write("Loading dashboard...")
    # Here we would import and show the main dashboard
    st.info("Full dashboard will be loaded here")
