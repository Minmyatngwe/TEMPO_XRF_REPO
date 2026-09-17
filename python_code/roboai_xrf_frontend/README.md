# RoboAI XRF Streamlit frontend

This frontend deliberately does **not** construct the Geant4 JSON directly.

Flow:

```text
Streamlit UI
    -> roboaixrf Python objects
    -> RoboAiXrfSimulation.compile()
    -> config.json
    -> Geant4 C++ backend
    -> simulation.root
    -> detector_noise()
```

## Files

```text
frontend/
├── main.py
├── theme.py
├── defaults.py
├── state.py
├── builder.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
└── components/
    ├── __init__.py
    ├── common.py
    ├── setup_page.py
    ├── tube_page.py
    ├── detector_page.py
    ├── physics_page.py
    ├── run_page.py
    └── results_page.py
```

## Install

Use the same Python environment in which `roboaixrf` is installed/importable.

```bash
pip install -r requirements.txt
python -c "import roboaixrf; print(roboaixrf.__file__)"
```

If `roboaixrf` is a local editable package, install that package in editable mode from
the package repository/root using the packaging command appropriate for that repo.

## Run

From this frontend directory:

```bash
streamlit run main.py
```

## Workflow

1. **Setup**
   - world material and dimensions
   - custom materials
   - sample

2. **X-ray tube**
   - source / target parameters
   - tube placement
   - tube window
   - SpekPy filters
   - physical Geant4 filters

3. **Detector**
   - active detector
   - housing
   - internal masks
   - detector filters
   - detector collimators

4. **Physics**
   - fluorescence / Auger / PIXE
   - biasing and secondary splitting
   - fluorescence data set
   - cuts and factors

5. **Build & run**
   - save run settings
   - Build & compile
   - optional visualization
   - quantitative Geant4 run
   - inspect/download generated `config.json`

6. **Results**
   - physical current/live-time scaling
   - detector noise
   - interactive spectrum plot
   - CSV export

## Important Streamlit/session behavior

`RoboAiXrfSimulation` keeps compile/run state in private in-memory attributes.
Therefore the app stores the live simulation object in `st.session_state`.

If the Streamlit server is restarted, compile and run the simulation again from the UI.

Changing geometry/material/physics inputs invalidates the current simulation object, so
you cannot accidentally run an old compiled configuration after changing the setup.

## Package workaround

At the time this frontend was built, `Placement.in_front_of_tube_window()` creates its
input using `Orientation` rather than the model field `orientation`. `builder.py`
therefore calls the package factory and, only if the returned orientation is missing,
sets:

```python
placement.orientation = Orientation(mode="inherient")
```

This can be removed once that package factory is corrected.
