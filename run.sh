source src/venv/bin/activate
pip3 install -r requirements.txt
cd src
python3 reddit_crawler.py
python3 src/index.py
python3 src/app.py
