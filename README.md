
# 🧠 Intelligent Database Query Assistant

A conversational AI-powered assistant that allows users to query relational databases using natural language — no SQL knowledge required! Built using LangChain, OpenAI, and MySQL, this system bridges the gap between non-technical users and structured data access.

## 🚀 Features

- 🔍 Query relational databases using plain English
- 🧠 Converts natural language to SQL using LangChain + OpenAI
- 🗃️ Executes real-time queries on a MySQL database
- 💬 Provides natural language responses and displays SQL on request
- 🕘 Maintains session-based chat history
- 🛠️ Handles errors and unclear queries with clarification prompts



## 🔧 Installation

### Prerequisites:
- Python 3.8+
- MySQL Server
- OpenAI API key
- (Optional) LangChain key if applicable

### Setup:

```bash
git clone https://github.com/your-username/database-query-assistant.git
cd database-query-assistant
pip install -r requirements.txt
```

Update `config.py` with:
```python
OPENAI_API_KEY = "your_openai_key"
DATABASE = {
    "host": "localhost",
    "user": "your_db_user",
    "password": "your_password",
    "database": "your_db_name"
}
```

Run the application:
```bash
python app.py
```

Access the interface at `http://localhost:5000`.

## 🧪 Testing

- Manual backend SQL verification using MySQL Workbench
- Query response validation through UI
- Chat history and clarification tested across multiple sessions

## 🐞 Known Issues

| Bug ID   | Description                                          | Status     |
|----------|------------------------------------------------------|------------|
| BUG-001  | No error message on incorrect DB credentials         | Fixed      |
| BUG-002  | Some chat histories fail to load completely          | Under Fix  |


## 🛠️ Built With

- [Python](https://www.python.org/)
- [LangChain](https://www.langchain.com/)
- [OpenAI GPT](https://platform.openai.com/)
- [Flask](https://flask.palletsprojects.com/)
- [MySQL](https://www.mysql.com/)

## 📈 Future Scope

- 🔄 Multi-turn conversation support
- 🎙️ Voice input capabilities
- 📊 Data visualization integration
- 🔐 Role-based access control
- 🌐 Cross-database compatibility (PostgreSQL, NoSQL)

## 👥 Contributors

- B.V. Dinesh Krishna  
- P. Yogendrasai  
- S. Rajeev  
- Guided by: Ms. Pooja Gowda  


