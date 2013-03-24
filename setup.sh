pip install --upgrade whenIO
if [ -d "$HOME/.scripts" ]; then 
    ln -sf `pwd`/schedule.py ~/.scripts
    ln -sf `pwd`/pinpoint.py ~/.scripts
    ln -sf `pwd`/filter.py ~/.scripts
fi
