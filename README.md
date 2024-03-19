# IMO---Sidecar-Networking
Install DockerDesktop.
Start DockerDesktop
If you are running a Grafana daemon on your local host, either stop it or change the port in the docker_compose.yaml

Run the following:
./run.sh

Continue once everything is up and running in DockerDesktop.

You may have some trouble if you are monitoring Prometheus and/or Jaeger from other sources 
since those ports may already be in use.

#set up Grafana add data sources
In your browser, go to http://localhost:3000 (or the port you set Grafana to use in docker_compose.yaml)
You will see a login page. If this is your first time, username and password are admin
You will be prompted for a password reset 

#add data sources
Once logged in, select Connections from the main menu and click on DataSources
1) Add datasource "Prometheus", set the url to http://host.internal.docker:16686, select "save & test"
2) Add datasource "Jaeger", set the url to http://host.internal.docker:4317, select "save & test"

#load dashboard
Select Dashboards from main menu
Under New, Select Import
Upload
./HelloWorld.json

The Dashboard should appear and you should see 2 active panels that show the stats traffic and the traffic from the 
dynamic envoy controller. The others will be blank because we haven't done anything to activate those metrics.

#run curl one successful
In Docker Desktop, 
	select ubuntu-curl container
	select the Exec tab
	type the following commands:
	    curl -k -v https://envoy-client:10000/usdeclar.txt
	    curl -k -v https://envoy-client:10000/constitution.txt

Take a look at the Grafana dashboard, You should see some change in the display. It may take a minute since the 
dashboard updates every 5s. You should see an increase in the http requests for both the envoys and an increase in 
the bytes sent and received by the sidecars.

#how to view tracing
The Traces panel should show a box for each curl request. To view the traces, select Explore from the panel. This 
will give you a list of traces. You should see 2. To explore the traces click on the TraceId of the trace. The trace 
information appears on the right.
