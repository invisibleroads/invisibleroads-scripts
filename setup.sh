pip install --upgrade whenIO
pip install --upgrade google-api-python-client
if [ -d "$HOME/.scripts" ]; then 
    ln -sf `pwd`/schedule.py ~/.scripts
    ln -sf `pwd`/pinpoint.py ~/.scripts
    ln -sf `pwd`/filter.py ~/.scripts
fi
