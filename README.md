# TravelTales
In-Car automatic conversation topic suggester



### Server deployment

Run the server.py script from the /Server directory.

You have to install ffmpeg codec at this link: https://www.gyan.dev/ffmpeg/builds/

For windows installation you can type in the powershell: `winget install "FFmpeg (Essentials Build)"`


#### Deployment on Docker using docker compose:

Upload the directory "Server" on the server running docker by using a command like:

```
scp -r /PATH/TO/THIS/REPO/Server remote_username@server_address:~/travel_tales_server
```

The Docker server needs docker-compose:
```
apk update
apk add docker-cli-compose
```
---

Then you have to build the docker pod:

run this command from the docker server in the directory where there is the docker-compose.yaml. (i.e. `~/travel_tales_server`):
```
docker compose build
docker compose up
```
---
The name of the generated docker container corresponds to the folder name where the docker-compose.yaml is located.
