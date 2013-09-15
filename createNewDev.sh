#!/bin/bash

cd /var/www

echo "Please enter the username(on the server) of the user: "
read username

echo "Please enter the username(on Github) of the user: "
read githubUsername

git clone git@github.com:Japan-Digital-Archives/Japan-Digital-Archive.git $username

cd $username

git fetch origin stable
git checkout stable
git remote rm origin
git remote add origin "git@github.com:$githubUsername/Japan-Digital-Archive.git"
git checkout -b $username
git push -u origin $username

cp ../ej/app/config/parameters.ini app/config/

cp ../ej/web/.htaccess web/

composer install

sudo setfacl -R -m u:www-data:rwx -m u:$1:rwx app/cache app/logs
sudo setfacl -dR -m u:www-data:rwx -m u:$1:rwx app/cache app/logs
