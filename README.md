# ElectroWorld Case Study Task
Done by Vojtech Poriz in April 2024 as part of Temus hiring process.

## Table of Contents
1. [Prerequisitiess](#prerequisities)
2. [Installation](#installation)
3. [Repository description](#) 
4. [Further information](#further-information)
***
## Prerequisities
- installed Docker

## Installation
1. Clone repository
```
git clone https://github.com/vojtooo/ElectroWorldCaseStudyPorizTemus
```
2. Build Docker image
```
docker build -t electroworld-app .
```
3. Run Docker image
```
docker run -p 5000:5000 electroworld-app
```

## Repository description
- `config_.py` - Configuration file
- `webserver_app.py` - Main flask app module
- `requirements.txt` - Description of necessary modules and versions
- `Dockerfile` - Docker configfile 
- `eda.ipynb` - Exploratory data analysis
- `temus_project_poriz.db` - Pre-saved database 

## Further information
[Google Slides Presentation](https://docs.google.com/presentation/d/1QR1P1pkSgZDcR4d-72HjHK0WgLZQkL7RdNLrVJA0biU/edit?usp=sharing)

