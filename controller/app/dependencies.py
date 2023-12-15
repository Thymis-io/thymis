from app.crud import state


def get_or_init_state():
    if not state.is_initialized():
        state.initialize()

    return state.load_from_file()
