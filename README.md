\# USA Chronic Disease Explorer



An interactive dashboard for exploring U.S. chronic disease data using Python, Streamlit, MongoDB, Pandas, and Plotly.



\## Features

\- Filter records by health topic, location, year, and data type

\- Search health-related questions and data values

\- Interactive charts and visualizations

\- View filtered records in a table

\- Download displayed records as CSV

\- Explore demographic data and confidence limits



\## Tech Stack

\- Python

\- Streamlit

\- MongoDB

\- PyMongo

\- Pandas

\- Plotly



\## Database

\- Database: chronicDiseaseDB

\- Collection: disease\_records



\## How to Run

1\. Install Python and MongoDB.

2\. Import the required dataset into MongoDB.

3\. Install dependencies:



&#x20;  pip install -r requirements.txt



4\. Run the dashboard:



&#x20;  python -m streamlit run app.py



5\. Open http://localhost:8501 in your browser.



\## Dataset

The dataset is not included in this repository. Import the required U.S. chronic disease dataset into MongoDB before running the application.

