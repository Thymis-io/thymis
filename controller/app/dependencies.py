from app.crud import state


def get_state():
    if not state.is_initalized():
        state.initalize()

    return state.load()
