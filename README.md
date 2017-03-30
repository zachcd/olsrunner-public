# olsrunner
Running the LoL@Pitt OLS Website

## Requirements to run:

 - Riot API Key  
 - Riot Tournament API Key  
 - [Python 3.5]  (https://www.python.org/downloads/)  

#### Installed using PIP  
 - Django [[Win]](https://docs.djangoproject.com/en/1.9/howto/windows/)[[Linux]](https://docs.djangoproject.com/en/1.9/topics/install/)  
 - [Django-tables2](https://github.com/bradleyayers/django-tables2)  
 - [Cassiopeia](http://cassiopeia.readthedocs.org/en/latest/genindex.html)    

## First time setup

 1. Install Python 3.5  
 2. Install Django  
    * `python -m pip install Django`
 3. Install Django-tables2 and cassiopeia with pip  
    * `python -m pip install django-tables2`
    * `python -m pip install cassiopeia`
 4. Add SECRET_KEY value to \olsrunner\ols\settings.py (this can be whatever you want)
 5. Run database migration commands  
    Navigate to \olsrunner\  
    * `python manage.py makemigrations`
    * `python manage.py migrate`
 6. Before all riotapi and baseriotapi in views.py and models.py, append riotapi.setkey or baseriotapi.setkey with your appropriate key
 7. Run website  
    * `python manage.py runserver`

