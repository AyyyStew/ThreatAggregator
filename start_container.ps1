docker build -t threat-aggregator .
docker run -d -p 80:80 -v ${pwd}/app/data:/code/app/data threat-aggregator 