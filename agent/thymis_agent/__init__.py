import logging

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, handlers=[ch])

# shared by all modules of the package; named after the original single-module
# agent so log records keep their logger name
logger = logging.getLogger("thymis_agent.agent")
