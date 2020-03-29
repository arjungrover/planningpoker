# PlanningPoker
This is the backend for the Planning Poker

# How to run the application
1. Install pip3
2. sudo apt-get install python3-pip
3. Install PSQL
4. Create virtual environment
    mkvirtualenv env-name
5. Activate the virtual environment
    workon env-name
6. Install requirements
    pip3 install -r requirements.txt
    sudo apt-get install redis-server
    sudo apt-get install rabbitmq-server
7. Clone the project from the gitlab:
    git clone https://github.com/arjungrover/planningpoker.git
8. Navigate to the directory planningpoker
9. Create a database in postgres and grant all privileges on database to the user
10. Run the migrations
    python manage.py migrate
11. Run the server
    python manage.py runserver
12. run the following command to deactivate the virtual environment
13. deactivate
