pip install -U whenIO
pip install -U google-api-python-client python-gflags
if [ -d "$HOME/.scripts" ]; then 
    ln -sf `pwd`/filter.py ~/.scripts
    ln -sf `pwd`/schedule.py ~/.scripts
    ln -sf `pwd`/pinpoint.py ~/.scripts
fi
