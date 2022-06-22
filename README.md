# task

Task for job interview
Привет! Рада тебя видеть)

Как запустить проект локально:
Установить PostgreSQL

bash: 
psql -U postgre

SQL Shell:

**CREATE DATABASE myprojectk;**

**CREATE USER myprojectuser WITH PASSWORD 'password';**

**ALTER ROLE myprojectuser SET client_encoding TO 'utf8';**

**ALTER ROLE myprojectuser SET default_transaction_isolation TO 'read committed';**

ALTER ROLE myprojectuser SET timezone TO 'UTC'; 
GRANT ALL PRIVILEGES ON DATABASE myproject TO myprojectuser;


открыть проект, созать вертуальную среду

ввести команду  
pip3 install -r requirements.txt

uvicorn app.main:app --reload

начнется стрим данных

телеграм канал:
https://telegram.me/job_task_bot

Если что-то пойдёт не так, то можно просто запустить файл
"Read_data.py" в папке app
Будет то же самое

Командой:
Python3 <file_path>

