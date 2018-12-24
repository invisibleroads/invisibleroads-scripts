InvisibleRoads Scripts
======================
Here are command-line scripts for managing your goals. ::

    vim ~/.invisibleroads/configuration.ini
        [editor]
        command = vim
        timezone = US/Eastern

        [database]
        # dialect = postgresql
        # username =
        # password =
        # host =
        # port =
        # name =
        dialect = sqlite
        path = ~/.invisibleroads/goals.sqlite

        [archive]
        folder = ~/.invisibleroads
        business.terms = business goals
        business.folder = ~/Projects/business-missions
        personal.terms = personal goals
        personal.folder = ~/Projects/personal-missions

   pip install -U invisibleroads-scripts
   invisibleroads edit

Database Configuration
----------------------
Here are the steps if you would like to configure a remote database. ::

   ssh your-machine
      # Install packages
      sudo dnf install -y postgresql-server
      # Initialize database server
      sudo postgresql-setup --initdb --unit postgresql
      # Start database server
      sudo systemctl start postgresql
      # Open port 5432
      sudo firewall-cmd --add-port=5432/tcp

      # Add database user
      sudo -s -u postgres
      psql
         \password postgres
         CREATE USER your-username WITH PASSWORD 'your-password';
         CREATE DATABASE your-database OWNER your-username;

      # Start database server on boot (optional)
      sudo systemctl enable postgresql
      sudo firewall-cmd --permanent --add-port=5432/tcp

   vim ~/.invisibleroads/configuration.ini
      [editor]
      command = vim
      timezone = US/Eastern

      [database]
      dialect = postgresql
      username = your-username
      password = your-password
      host = your-machine
      port = 5432
      name = your-database

      [archive]
      folder = ~/.invisibleroads
      business.terms = business goals
      business.folder = ~/Projects/business-missions
      personal.terms = personal goals
      personal.folder = ~/Projects/personal-missions
