#!/bin/sh
cd /var/www/html

if test -f "composer.json"
then
    /usr/bin/composer install
fi

php-fpm -F
