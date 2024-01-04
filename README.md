# CarthographRL
## Requirements
- web-based UI
- support solo playing against AI
- support visualization of AI self-play
- support getting hints from AI by providing the next cards
- different RL algorithms to apply
- Monte Carlo Tree search
- gymnasium interface

## Repo structure
carthograph_rl
├── model
│   ├── gym_env.py
│   ├── cartograph_model_base.py
│   ├── implementations
│   │   ├── cartograph_model_v1.py
│   │   ├── cartograph_model_v2.py
│   │   ├── ...
│   ├── game_assets
│   │   ├── actioncards.json
│   │   ├── scoringcards.json
│   │   ├── maps.json
├── app
│   ├── __init__.py
│   ├── static
│   │   ├── css
│   │   ├── js
│   │   ├── img
│   ├── templates
│   │   ├── index.html
├── utils

## Design Decisions
- The `gym_env.py` gets an implementation object of the cartograph game and wraps it with gym interface. This way we can have different implementations of the cartograph game and use them in the same gym environment. Also the we have the model separated from the gym environment, which we only need for the RL part.
- How to strucuture/place/save the game assets? (maps, action cards, scoring cards): 

## Model Perofrmance Optimization
- most exploration option are very symmetric --> precompute possible transformations and thereby reduce action set for mcts