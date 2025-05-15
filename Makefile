rebuild:
	docker-compose run --rm --build userbot
run:
	docker-compose run --rm userbot
build:
	docker-compose build userbot --no-cache
