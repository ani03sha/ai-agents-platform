"""Shared library for the AI Agents Platform.

Holds the pieces both services depend on: structured logging configuration,
JWT auth helpers, and the cross-service event and task models. Deliberately
infrastructure-light, no FastAPI, no DB drivers, so the worker and the API
can both import it without dragging in each other's dependencies.
"""

__version__ = "0.1.0"
