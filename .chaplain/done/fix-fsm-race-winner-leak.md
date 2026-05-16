fix(fsm): run_and_dispatch leaks _race_winner into FSM event payload (#395)

Race and router-race nodes inject `_race_winner` metadata into graph state. `run_and_dispatch` does not strip this key before building the event payload. Strip `_race_winner` from result dict before payload construction and log the stripped value at INFO level.
