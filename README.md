# Amusement Park Simulation 

This project simulates the operations and behaviours inside an amusement park. It models how hundreds of visitors enter the park, make decisions, ride attractions, eat at food trucks, use bathrooms, buy merchandise, and move as social groups. The simulation is fully multi-threaded to represent many independent activities happening concurrently, such as facility operation, visitor behaviour, and arrivals over time. A real-time user interface visualizes the ongoing activity inside the park.

## Features
### Visitors

Hundreds of autonomous visitors with individual attributes such as height, hunger, energy, spending habits, and ride preferences.
Three base visitor types: Child, Tourist, and Adrenaline Addict, each with unique behaviours.
Optional social visitor mode where visitors belong to predefined groups (families, couples, friends) and coordinate actions such as following a leader or waiting for each other.
Each visitor operates in its own thread, making decisions in parallel.

### Rides & Attractions

A variety of rides, each with capacity, duration, height requirements, and a probability of breaking down.
Rides operate on independent threads, continuously cycling through loading, running, and unloading phases.

### Food Trucks & Merchandise Stands

Multiple food trucks that simulate serving visitors and generate revenue.
Merchandise stands that allow visitors to purchase souvenirs.
Each operates in a dedicated thread and manages its own queue.

### Bathrooms

Several bathrooms running in their own threads, each serving visitors one at a time.
Fully integrated with the visitor behaviour and queueing system.

### Arrival System

Visitors enter the park over time based on a Poisson arrival distribution, handled by a dedicated arrival generator thread.

### Real-Time UI

A live, dynamic user interface that displays:
- Ride status and queue lengths
- Food truck and merch stand activity
- Bathroom usage
- Visitor statistics
- Park-level summaries


## Requirements
It is necessary to install the requirements that can be found in the requirements.txt file

- pip install -r requirements.txt 

## File Structure
Core Logic

- `main.py` : Entry point of the simulation. Initializes the park, resources, visitors, arrival generator, and UI.

- `park.py`: Central coordinator managing rides, facilities, visitors, and queue operations.

- `clock.py`: Global time controller for simulated minutes and stopping conditions.

- `queue.py`: Thread-safe queue implementation used by rides, food trucks, bathrooms, and merch stands.

- `simple_social_visitor.py`: Defines the base visitor types (Child, Tourist, AdrenalineAddict) and their behaviours. Handles Group logic.

- `simple_social.py`: Implements social groups, location tracking, and group coordination logic.

- `ride.py`: Ride operations, including loading, running, breakdowns, and maintenance.

- `food.py`: Food truck logic and service behaviour.

- `staff.py`: Implements the different kind of staff in the park and their behaviour. 

- `merch.py`: Merchandise stand operations.

- `metrics.py`: Tracks and store the metrics of the simulation. 

- `bathroom.py`: Bathroom handling and queuing logic.

- `arrival_generator.py`: Generates and starts visitors over time using Poisson arrival patterns.

- `park_ui.py`: Implements the real-time graphical interface for monitoring the simulation.

- `park_metrics.sqlite`: Store the data of the simulation.

- `view_metrics.py`: Read the data in the SQLite database.

## Ideas for Future Improvements

- Optimize thread management for very large visitor populations.

- Add spatial movement with paths and travel time between attractions.

- Improve the UI to show visitor movements and group formations visually.

- Introduce dynamic events (weather changes, parades, showtimes).

- Extend social behaviour with spontaneous friendships or crowd effects.

