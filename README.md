# ChatDB [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://chat-db.streamlit.app/)
A web app built with [Streamlit](https://streamlit.io/) that allows you to chat with your databases using a GPT model.

## Features
- Chat with your [GPT model](https://platform.openai.com/docs/models) of choice
- Ask about anything in your databases, and the bot will answer
<img src="https://github.com/SutandoTsukai181/ChatDB/assets/52977072/3487c47f-8f1e-415b-9e42-ad9c5e0c2e13" width="600">

&nbsp;
- View the results *and* the SQL queries that the GPT model generated
  - SQL queries are added below the bot's response
  - <img src="https://github.com/SutandoTsukai181/ChatDB/assets/52977072/d0307223-fbe1-405b-bae5-e1c170a15faf" width="600">
  &nbsp;
  - Expand the box to see the query and the result the bot received
  - <img src="https://github.com/SutandoTsukai181/ChatDB/assets/52977072/1d84dd40-cb69-4abc-b034-522249397176" width="600">
  &nbsp;
  - If the model accidentally generates an invalid query or the query fails, the error will be displayed (example: `apartments` table is not in the database)
  - <img src="https://github.com/SutandoTsukai181/ChatDB/assets/52977072/7b259881-f22b-426a-a9ef-10030393d5e7" width="600">
  &nbsp;
  - GPT 3.5 turbo (the default model) is really good at generating complex SQL queries from your questions, so just ask away!
  - <img src="https://github.com/SutandoTsukai181/ChatDB/assets/52977072/c130b1f6-c25c-4afe-8b18-4ee49edef2a1" width="600">
&nbsp;
- Locally backup and restore your conversations and settings (API keys are encrypted before backup)
<img src="https://github.com/SutandoTsukai181/ChatDB/assets/52977072/5277cdcc-52ba-4dd3-8713-9fc4e2b457e7" width="600">

## Getting started
- Open the [Streamlit app](https://chat-db.streamlit.app/) in your browser: [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://chat-db.streamlit.app/)
- Go to the **⚙️ Settings** page
- Provide your OpenAI API key and add some database connnections
- Go to the **🤖 Chats** page
- Create a new conversation by specifying the GPT model and selecting the databases you added
- Start chatting 🗣 ↔️ 🤖

## Compatibility
Currently supported databases:
- PostgreSQL (using `psycopg2`)
- MySQL and MariaDB (using `mysqlclient`)
- Microsoft SQL Server (using `pyodbc`)

**If your database or DB API are not here, feel free to open a feature request. Contributions are also very welcome!**

## Building
If you want to build and test locally:
- Clone the repository
- Install requirements with `pip install -r requirements.txt` (recommended to use a virtual environment)
- Launch the app with `streamlit run 🏠_Home.py`

## Acknowledgement
- [Streamlit](https://streamlit.io/)
- [LlamaIndex 🦙](https://www.llamaindex.ai/)
- [LlamaHub 🦙](https://github.com/emptycrown/llama-hub)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [UI Bakery SQL playground](https://uibakery.io/sql-playground)

This project is part of an internship I performed at [B.E.A.R. TELL](https://beartell.com).
