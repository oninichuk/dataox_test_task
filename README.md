# dataox_test_task
## Warning:
Considering fact that Financial Times set articles limit per month, it made impossible to retrieve articles web pages but I implemented all necessary features using articles that I got before(when I didnt exceed limit). System will not get valid articles web pages due to reading limit, so it will cause fail of parsing/saving articles. I didn't use any kind of Proxy, implemented only technical part, it will work correctly in case of solving articles limit problem.

## Introduction
System was implemented as django project which integrates with such libraries like asyncio, aiohttp(asynchronous requests), selenium
There are 2 management commands "fetch_articles_aiohttp", "fetch_articles_selenium", each of them represents own variant of fetching articles. `Please estimate both commands.` 
Default fetching command is "fetch_articles_aiohttp" that is running by Celery Beat every hour. You can change active fetching command in .env file, you should use `ACTIVE_FETCH_COMMAND` variable. Also you can access to DB via admin panel or Rest API which was implemented separately.

## Before install. Configuration
Before installing you should create your own .env file using .env.example:
```
cp .env.example .env
```
In this file you can set values for settings like `ACTIVE_FETCH_COMMAND`

## Installation
You should have preinstalled `docker compose`.
Clone this repository to your local machine via "git clone" or using features of your code editor.

Go to main directory(cloned from repository):
```
cd /path/to/main/directory
```

Build docker images:
```
docker compose build
```

Before first run of docker containers you should import database dump.
First of all run db service separately:
```
docker compose up -d db
```
You should wait some time until db service fully started(healthy condition)

Then you can import database dump:
```
docker compose exec db psql -U ft_user -d ft_db -f dump.sql
```
#### Note: `ft_user` - db username, `ft_db` - db name. If you changed these values in .env file then you should adjust command accordinally

## First run
Now you can run all services
```
docker compose up -d
```
After all services started fetching command will run periodically every hour. You can access to django project using link http://localhost:8022

## Tests
You can run specific test separately(method of tests.ArticleTestCase class). For example method "test_parser_manager":
```
docker compose exec django_project python manage.py test main_app.tests.ArticleTestCase.test_parser_manager
```
Or you can run all tests:
```
docker compose exec django_project python manage.py test main_app.tests.ArticleTestCase
```
#### Note: If you runned all docker containers via `docker compose up -d` you should use `docker compose exec`, if not then execute `docker compose run`

## API
Rest API was implemented using Django Rest Framework. I used ModelViewSet for proving all necessary CRUD operations like INSERT, UPDATE, DELETE
You can access to all operations using following endpoints:
```
GET	/api/articles/	List all articles
POST	/api/articles/	Create new article
GET	/api/articles/<id>/	Retrieve article
PUT/PATCH	/api/articles/<id>/	Update article
DELETE	/api/articles/<id>/	Delete article
```

## Logging
I implemented logger which adds logs to file `scraping_project/logs/django.log`

## Django admin panel
You can access to admin panel using these credentials:
```
login: ft_django_user
email: random@someservice.com
password: somerandom2025
```
