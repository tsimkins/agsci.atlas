#!/bin/bash

lynx -dump -source http://localhost:6061/atlas/@@api-sample/json > sample.json
lynx -dump -source http://localhost:6061/atlas/@@api-sample > sample.xml
