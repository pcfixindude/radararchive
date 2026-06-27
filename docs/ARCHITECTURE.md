# Architecture

## Principle
The phone app is only a viewer. All collection and processing happens in the cloud.

## System
NOAA/AWS data sources → collector worker → raw storage → processor worker → processed storage → catalog database → API/tile server → PWA/mobile app.

## Backend
FastAPI provides API endpoints. Workers collect and process radar data. Database indexes products, timestamps, files, users, and access plans.

## Frontend
Mobile-first PWA using MapLibre or Leaflet. The map requests tiles and vector layers from the backend.

## Data Rule
Raw source files are immutable. Processed files can be regenerated. Database records point to both raw and processed paths.
