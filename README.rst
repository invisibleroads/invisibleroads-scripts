InvisibleRoads Scripts
======================
Here are command-line scripts for managing your goals. ::

    pip install -U invisibleroads-scripts
    invisibleroads edit
        Eat
        Exercise
            Do 10 pullups
            Do 20 pushups
            Do 30 jumps
        Sleep
    invisibleroads edit -A            # Include archived goals
    invisibleroads edit your-keyword  # Filter by keyword
    invisibleroads edit your-goal-id  # Focus on specific goal
        # Mission
            Specify a goal
        # Log
            Record notes
        # Schedule
        20181225
            Schedule goals by date using YYYYMMDD
        # Tasks
            List remaining tasks using nested indent

Script Configuration
--------------------
Here are optional steps to configure your scripts. ::

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

      # Add database user
      sudo -s -u postgres
         psql
            CREATE USER your-username WITH PASSWORD 'your-password';
            CREATE DATABASE your-database OWNER your-username;

      # Configure database access
      sudo -s -u postgres
         psql
            \password postgres
            show hba_file;
      sudo vim /var/lib/pgsql/data/pg_hba.conf
         host your-database your-username your-ipv4 md5
         host your-database your-username your-ipv6 md5
         # host your-database your-username 0.0.0.0/0 md5
         # host your-database your-username ::0/0 md5
      sudo vim /var/lib/pgsql/data/postgresql.conf
         listen_addresses = 'your-ip'
         # listen_addresses = '*'
      sudo systemctl restart postgresql

      # Open database port
      sudo firewall-cmd --add-port=5432/tcp

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
