#!/bin/bash
dbname="users"
username="imo"
password="123456"
configDir="/tmp"
port=5984

# Wait for CouchDB to be up
echo "Waiting for CouchDB to start..."
while ! curl -s http://localhost:5984/ > /dev/null; do
  sleep 1
done
echo "CouchDB started."

if curl -s -X GET "http://$username:$password@localhost:5984/_all_dbs" | grep -q "\"$dbname\""; then
  echo "Database $dbname exists, deleting it"
  curl -X DELETE "http://$username:$password@localhost:5984/$dbname"
fi

echo "Building $dbname DB"
sleep 5
echo "curl -X PUT http://$username:$password@localhost:5984/$dbname"
curl -X PUT "http://$username:$password@localhost:5984/$dbname"
echo "Manually add _users database"
curl -X PUT "http://$username:$password@localhost:5984/_users"

echo "converting all Envoy configs to json files"
pushd $configDir > /dev/null
for file in $(find . -type f -name "*.yaml"); do
	name=$(basename "$file")
    echo "Processing $name"
    python3 -c 'import sys, yaml, json; json.dump(yaml.safe_load(sys.stdin), sys.stdout, indent=4)' < "$file" > "${file%.yaml}.json"
done
popd > /dev/null

echo "Adding configs to DB"
pushd $configDir > /dev/null
for file in $(find . -type f -name "*.json"); do
	name=$(basename "$file")
    echo "Processing $name"
	id="${file%.json}"
    curl -X PUT -H "Content-Type: application/json" -d @"$file" "http://$username:$password@localhost:5984/$dbname/$id"
done
popd > /dev/null

echo "adding secrets..."
curl -X PUT -d '{"envoy_client":"client_pass","envoy_server":"server_pass"}' "http://$username:$password@localhost:5984/$dbname/secrets"