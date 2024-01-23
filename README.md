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
│   ├── static
│   │   ├── css
│   │   ├── js
│   │   ├── img
│   ├── templates
│   │   ├── index.html
├── utils

## Design Decisions
- The `gym_env.py` gets an implementation object of the cartograph game and wraps it with gym interface. This way we can have different implementations of the cartograph game and use them in the same gym environment. Also the we have the model separated from the gym environment, which we only need for the RL part.
- The format of the game assets is choosen so that it is easy to add the assets. Any conversions for performance reasons can be done in the implementation of the cartograph game. For example, the maps are stored as a list of lists, but the implementation can convert it to index based hash map for faster access.
- The exact format (names of attributes etc.) are specified by using pedantic dataclasses. This way we can easily serialize and deserialize the dataclasses to json and back. Also we can use the dataclasses as type hints for the functions. The classes representing the game assets do not contain any logic and are only used to store the data. The logic is implemented in the implementation of the cartograph game and can be dfifferent for different implementations.
- Monster cards, ruin cards, normal cards: These cards are all "exploration cards". However they serve different purposes and are also played differntly. Temple cards do not contain any dedicated information. It is therfore not necessary to save them as an assets. Rather the number of ruin cards in the deck needs to be specified somewhere. Monster cards however can be seen as a special type of normal exploraation casrds which also contain additional information on the attack (rotation direction). However as the mosnter cards behave completely differently and there might be additional mechanism added to monsters in future it seems to make more sense to have a dedicated monster card class instead of subclassing the normal exploration card class. Consequently we also create a new asset file and a new pedantic dataclass for the monster cards.
- Monster cards are named Ambush cards to be consistent with the game rules.


## Model Performance Optimization
- most exploration option are very symmetric --> precompute possible transformations and thereby reduce action set for mcts