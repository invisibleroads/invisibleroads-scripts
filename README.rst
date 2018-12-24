InvisibleRoads Scripts
======================
Here are command-line scripts for managing your goals. ::

    pip install -U invisibleroads-scripts

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
