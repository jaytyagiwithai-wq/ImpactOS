We intend to run two containers, but we only have one Docker Compose file. The second YAML file configures the Collector application.

we have docker compsoe fiel where we define two services

compose groups its container, netwroks adn vols

1. The clickhouse serivce is used to persist telemetry data and execute analytical query

2. The collector receieves, processes , buffers and exports telemetry data

for clickhouse serivce using image we selcect the software artifcat 

for the collector we used - opentelemetry-collector-contrib coz it includes the clickhouse exporter

In clickhouse service we give the clcikhouse env vars which docker passes into the clickhouse container. The image's setup scirpts  uses it to configure database adn user.


The otel serivce- 
depends_on:
    clickhouse:
        condition: serivce_healthy

the otel serive waits for tehe clickhise health check before stating. This avoids statritng th exporter while desitnation is still intializing


---------


in seocnd compse file we ocnfidure the optel container using bind moounts- 

receivers - 
define how telemetry enter the colleciton

OLTP is open telemtrys transpoirt protocol.
The receivers accepts telemetry produced by instrimetnaiton 


memory-limiter-

provides backpressure under memory pressure
The processor periodically checks memory. Above the soft threshold, it refuses incoming telemetry with a retryable error. Above the hard threshold, it also forces garbage collection.

exporter- 
definers sotre adn schema beahvior 

