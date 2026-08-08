# Alembic
Alembic is the migration tool meant to be used aside the SQLAlchemy ORM.

## Setup
Setup process is simply executed through 2 steps:
- Package Installation: 
    - Package manager installation command (in the project's virtual environment) : ```pip install alembic```
    - This will additionally make its CLI available <br><br>

- Tool Initialization <br>

  - Alembic initialzation is triggered through the CLI command: ```alembic init alembic``` <br>

  - This creates a directory called ```alembic``` (named after the last argument of the previous command)
    - Inside the directory, there is a crucial script, called ```env.py```.
    - It serves as the configuration hub and the entry point of database migrations.
    - It is executed every time an Alembic command is run. 
     <br><br>
    - Before starting the application, that script has 2 important elements to make Alembic aware of: <br>

      - Database URL:
        - This line should be added in the script for this purpose: <br>
        ```config.set_main_option("sqlalchemy.url", DATABASE_URL)```
        - ```DATABASE_URL``` is the string variable that contains the exact URL of the database. <br>

        - You import it from the model it is defined in. <br>

        - This enables the connection of Alembic to the database it will interact with. <br>
        
      - SQLAlchemy models
        - You let Alembic know about your SQLAlchemy defined models by importing the modules where they are declared:
          - ```from models import auth, operations```
      
      - MetaData object declaration
        - This is an important mean that enables Alembic to compare the database schema with SQLAlchemy models.
        - It is an attribute of SQLAlchemy's ```Base``` class. 
        - Its declaration stands on the ```target_metadata``` variable in ```env.py``` script.
        
        - To properly accomplish this configuration, we follow this steps:
            - At first, we import the ```Base``` class from the database configuration module, where it is declared:
              - i.e: ```from database import Base```
            - Then, we overwrite the ```target_metadata``` variable assignment in ```env.py``` as:
              - ```target_metadata = Base.metadata``` 