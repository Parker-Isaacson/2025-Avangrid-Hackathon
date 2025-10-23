# 2025-Avangrid-Hackathon

This project consists of a results directory, which is the compilation of all the work we've done into a simple presentable format.

### Results

NA

### Pipeline order

If you wish to generate the results that we used, you will need to run the python files. Below are the steps to do this.

- Set up a python venv.
```powershell
# If you are on windows
python -m vevn Hackathon
.\Hackathon\Scripts\activate.ps1
pip install -r requirements.txt
```
```bash
# If you are on linux
python -m vevn Hackathon
source Hackathon\bin\activate
pip install -r requirements.txt
```
- Run `parse.py` in `data/` to generate some clean CSV data for later use. \
    - This can be done in by running `python data\parse.py` on windows, or `python data/parse.py` on linxu, from the root of the github repo.
- Run `analize.py` in `analysis/` to generate some more CSV data and some useful graphs.
    - This can be done in by running `python analysis\analize.py` on windows, or `python analysis/analize.py` on linxu, from the root of the github repo.
- Run `risk.py` in `analysis/` to computre risk adjustments.
    - This can be done in by running `python analysis\risk.py` on windows, or `python analysis/risk.py` on linxu, from the root of the github repo.