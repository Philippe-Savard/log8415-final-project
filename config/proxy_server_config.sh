#!/bin/bash
# Greatly inspired from https://www.rosehosting.com/blog/how-to-deploy-flask-application-with-nginx-and-gunicorn-on-ubuntu-20-04/ 
# and https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-16-04 
apt-get update -y
apt-get install python3 python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools -y
apt-get install nginx -y
apt-get install gunicorn3 -y
systemctl start nginx
systemctl enable nginx

mkdir /home/ubuntu/flaskapp
cd /home/ubuntu/flaskapp

# Install python dependencies
pip install sshtunnel
pip install PyMySQL
pip install wheel
pip install flask
pip install pythonping
pip install paramiko

# Get the flaskapp.py file from the git repository
wget https://raw.githubusercontent.com/Philippe-Savard/log8415-final-project/main/app/flaskapp.py

echo "
from flaskapp import app
if __name__ == \"__main__\":
    app.run()
" >> wsgi.py

# Deactivate current python venv
deactivate

# Obtain hostname of the machine through meta-data service offered by amazon
current_host=$(curl http://169.254.169.254/latest/meta-data/public-hostname)

# Flaskapp service configuration
echo "
[Unit]
Description=Gunicorn instance to serve flaskapp
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/flaskapp
ExecStart=/usr/bin/gunicorn3 --workers 3 --bind 0.0.0.0:5000 wsgi:app
[Install]
WantedBy=multi-user.target
" >> /etc/systemd/system/flaskapp.service

chown -R ubuntu:www-data /home/ubuntu/flaskapp
chmod -R 775 /home/ubuntu/flaskapp

systemctl daemon-reload
systemctl start flaskapp
systemctl enable flaskapp

echo "
server {
    listen 80;
    server_name \${current_host};

    location ^/direct {
        include proxy_params;
        proxy_pass http://localhost:5000/direct/;
    }

    location ^/random {
        include proxy_params;
        proxy_pass http://localhost:5000/random/;
    }
        
    location ^/random {
        include proxy_params;
        proxy_pass http://localhost:5000/custom/;
    }


    location ~* ^/(.*) {
        include proxy_params;
        proxy_pass http://localhost:5000/\$1\$is_args\$args;
    }
}
" >> /etc/nginx/sites-available/flaskapp

sudo ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled

systemctl restart nginx

# gunicorn configuration seems to fail at binding 0.0.0.0 sometimes, 
# manually starting flaskapp for testing
flask run --host=0.0.0.0
