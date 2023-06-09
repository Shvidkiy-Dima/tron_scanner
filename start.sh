#!/bin/bash

#!/bin/bash


sleep 2

python /app/check_conn.py --service-name db --port 5432  --ip db


python load_to_db.py
python main.py
