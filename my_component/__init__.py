import os
import streamlit.components.v1 as components

# Set this to True for production (static build), False for dev (npm run start)
_RELEASE = True

if not _RELEASE:
    # For development: use live Vite server (`npm run start` must be running!)
    _component_func = components.declare_component(
        "my_component",
        url="http://localhost:3001",
    )
else:
    # For production: use static build directory
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend", "build")
    print("COMPONENT BUILD DIR:", build_dir)
    _component_func = components.declare_component(
        "my_component",
        path=build_dir
    )

def my_component(name, key=None):
    print("my_component called with:", name)
    return _component_func(name=name, key=key, default=0)
