docker compose down;
docker build --build-arg path=./chnode1 -t chnode1 .;
docker build --build-arg path=./chnode2 -t chnode2 .;
docker build --build-arg path=./chnode3 -t chnode3 .;