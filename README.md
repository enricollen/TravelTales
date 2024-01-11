# TravelTales
In-Car automatic conversation topic suggester



## News Player Interface

![image](https://github.com/enricollen/TravelTales/assets/63967908/62044e29-1920-48ab-8a0c-247f30672080)


## Feedback gathering

![image](https://github.com/enricollen/TravelTales/assets/63967908/c1e8830b-1a76-4c54-8ce3-05b03607fca0)

## Data Visualization

![image](https://github.com/enricollen/TravelTales/assets/63967908/1d3011fa-538a-4d05-8193-d4b4a69eaad0)


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

### Client 
For the registration of a new user:
- open a web browser and visit: `server_ip_addr:5000`

Alternative:
- set the environment variable `DEFAULT_WEB_BROWSER` inside `Client/.env` and specify the path of the preferred browser to use:
```
# MacOS
DEFAULT_WEB_BROWSER = 'open -a /Applications/Google\ Chrome.app %s'

# Windows
DEFAULT_WEB_BROWSER = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'

# Linux
DEFAULT_WEB_BROWSER = '/usr/bin/google-chrome %s'
```
  then start the client GUI and click on Register button. It will prompt to the registration page on the desired browser.
