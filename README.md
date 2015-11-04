# QuantHoops
[March Madness](http://www.ncaa.com/march-madness) simulation with web scrapper modules and a database implementation.
# Description
A Python application to store all NCAA men/women basketball Web-based statistics in database. It will run each process daily by default. Relies on [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/), [SQLAlchemy](www.sqlalchemy.org/) and MySQL database.
# Files
* **ncaa.py**: Object model using SQLAlchemy. Database stores information about games, players, and teams interconnectly with rich docstring. Include this module in any script that needs to access DB. 
* **scraper.py**: Main module for scapping ncaa website. Follow the database structure to fill in data. Be able to ignore or fix errors from ncaa website.
* **fix.py**: This module will check database for bad records and try to fix them. Usually they were caused by known ncaa bugs.
* **scheduler.py**: Schedule how scraper will work, along with some command line interface.
