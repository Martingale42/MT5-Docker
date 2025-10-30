build:
	docker build -t mt5zmq .

run: build
	docker run --rm -dit -p 5900:5900 -p 2201:2201 -p 2202:2202 -p 2203:2203 -p 2204:2204 --name mt5zmq -v mt5zmq:/data mt5zmq

shell:
	docker exec -it mt5zmq bash

stop:
	docker stop mt5zmq

clean:
	docker rm -f mt5zmq
	docker volume rm mt5zmq
