import streamlit as st

st.set_page_config(
    page_title="Home",
    page_icon="🏠",
)

st.markdown(
    """
# ChatDB
A web app built with [Streamlit](https://streamlit.io/) that allows you to chat with your databases using a GPT model.

## Getting started
Start by adding a vector store and some database connections in the *⚙️ Settings* page.

- Go to the **⚙️ Settings** page
- Provide your OpenAI API key, and add a vector store and some database connnections
- Go to the **🤖 Chats** page
- Create a new conversation by specifying the GPT model and selecting a vector store and database connections
- Start chatting 🗣 ↔️ 🤖

## Contribution
Check the [repository on GitHub](https://github.com/SutandoTsukai181/ChatDB) and feel free to contribute!
Suggestions, feature requests, and issue reports are more than welcome.

This project is part of an internship I performed at [B.E.A.R. TELL](https://beartell.com).
"""
)
