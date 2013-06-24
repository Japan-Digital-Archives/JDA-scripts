#!/bin/bash

cd /var/www

git clone git@github.com:Japan-Digital-Archives/Japan-Digital-Archive.git $1

cd $1

git fetch origin stable
git checkout stable
git checkout -b $1

cp ../ej/app/config/parameters.ini app/config/

cp ../ej/web/.htaccess web/

composer install

sudo setfacl -R -m u:www-data:rwx -m u:$1:rwx app/cache app/logs
sudo setfacl -dR -m u:www-data:rwx -m u:$1:rwx app/cache app/logs
