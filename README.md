# TravelTales 🚗💬
Welcome to the documentation for TravelTales, your go-to in-car conversation recommendation system! 🌟

Explore the innovative TravelTales system, a solution balancing in-car entertainment with driver safety. Leveraging AI and ML, TravelTales provides personalized conversation prompts, enhancing the overall driving experience. 🚀

Introducing TravelTales, an in-car conversation recommendation system. Using AI, ML, and voice recognition, it creates personalized conversation prompts for an engaging and safe journey.

## State of the Art
Delve into conversation engagement monitoring, drawing inspiration from Morreale et al.'s multimodal approach. Our project adopts a similar strategy, integrating audio sentiment, speech rate, and video sentiment for dynamic engagement estimation.

## Architecture
Discover the client-server structure of TravelTales. The client, implemented in Python, runs on a Raspberry Pi, while the server, built with Python Flask, handles requests and responses. The indexer, created in Google Colab, uses GPUs for efficient processing.

## Indexer
Explore the comprehensive Indexer module, where the collection of news is created, including the TTS model, Summarization model, and News Embedding model.

### TTS Model
Utilizing Coqui TTS, TravelTales generates natural-sounding audio news tracks. The TTS model creates audio from news article summaries, enhancing the in-car experience.

### Summarization Model
The summarization model uses Latent Semantic Analysis and a BART Transformer for concise news summaries. Explore the application of these techniques through a sports news example.

### News Embedding Model
Learn about the news embedding model's real-valued vector generation from textual input. Based on a DistilBERT model, it maps news articles into a 14-dimensional space for effective similarity calculations. Operations include summarization, embedding creation, and audio generation from news articles.

## Server
Implemented in Flask, the server handles user registration, audio processing, news suggestions, and feedback. Explore endpoints for user interactions and data retrieval.

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

## Client 
For the registration of a new user:
- open a web browser and visit: `https://server_ip_addr:5000`

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

### Engagement Level Regressor
Learn about the heuristic-based engagement level estimation, considering speech rate, sentiment, and audio duration.

### Speaker Recognition Module
Discover the real-time speaker recognition module using Picovoice Eagle API, capturing and storing speaker-specific speech segments.

### Audio Sentiment Classification
Explore the module predicting sentiment from audio files, leveraging a pre-trained CNN for sentiment analysis.

### Data Visualization Module
This module provides a GUI for data visualization, showcasing PCA and radar chart plots to represent user interests and news categories.
![image](https://github.com/enricollen/TravelTales/assets/63967908/1d3011fa-538a-4d05-8193-d4b4a69eaad0)

### News Player Interface

![image](https://github.com/enricollen/TravelTales/assets/63967908/62044e29-1920-48ab-8a0c-247f30672080)


## Feedback gathering

![image](https://github.com/enricollen/TravelTales/assets/63967908/c1e8830b-1a76-4c54-8ce3-05b03607fca0)

## Further Improvements
While TravelTales presents a significant advancement, future enhancements could involve iterative updates based on passenger feedback. This approach ensures continual adaptability, refining the accuracy and relevance of personalized conversation prompts. The challenges of obtaining a suitable dataset for training an updating model and tuning the update process parameters must be addressed for successful implementation. Feel free to embark on a journey with TravelTales! 🌐🗣️




