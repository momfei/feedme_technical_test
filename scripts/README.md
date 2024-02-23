## Instructions
### Prerequisites
1.) Installed Python 3.10 https://www.python.org/downloads/

2.) Installed necessary Python libraries. Run `pip install -r requirements.txt `.

3.) Installed PostgreSQL with version 13 or above on your local machine.


### Instructions
1.) Create a database name as `ANXJDF`

2.) Run `table_creation.sql` to create necessary schema, types & tables in `ANXJDF` database.

3.) Open `mongodb_listener.py` in editor and update **mongo_uri** & **pg_conn_params** accordingly.

4.) Open command prompt and execute the Python script with `py mongodb_listener.py` or `python mongodb_listener.py`

5.) Validate the data by using `data_validation.sql`
