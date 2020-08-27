ECHO OFF

REM set BASEPATH to the python install on your machine that has dispy installed
set BASEPATH=C:\Users\jcherr01\OneDrive - Environmental Protection Agency (EPA)\Documents\Jeff Documents\GitHub\EPA_OMEGA_Model\venv\

REM location of python.exe (in Scripts path for venvs, else in basepath for straight install):
set PYTHONPATH=%BASEPATH%Scripts\

REM location of dispy package:
set DISPYPATH=%BASEPATH%Lib\site-packages\dispy\

REM how many cpus to serve (e.g. number of cores minus one)
set NUM_CPUS=7

ECHO ON
"%PYTHONPATH%python" "%DISPYPATH%dispynode.py" --clean --cpus=%NUM_CPUS% --client_shutdown --ping_interval=15 --daemon --zombie_interval=1